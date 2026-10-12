/* Bedrock 1.21.90+ / @minecraft/server 2.0.0.
 * A *block* Waystone; the old entity is retained only for non-destructive
 * migrations. Uses the existing v1 record format for activated destinations.
 */
import { world, system } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";

const BLOCK = "minizin:andesite_waystone_block";
const LEGACY = "minizin:andesite_waystone";
const KEY = "minizin:waystones_world_v1";
const KNOWN = "minizin:waystones_known_v1";
const LEGACY_ID = "minizin:waystone_id";
const busy = new Set();
const recent = new Map();
const DIRECTION = [[1,0],[-1,0],[0,1],[0,-1]];
const read = (holder,key) => {
  try {
    const text = holder.getDynamicProperty(key);
    return typeof text === "string" && Array.isArray(JSON.parse(text))
      ? JSON.parse(text) : [];
  } catch { return []; }
};
const save = (holder,key,records) => {
  const raw = JSON.stringify(records);
  if(raw.length > 30000) throw Error("Limite de armazenamento dos marcos atingido.");
  holder.setDynamicProperty(key,raw);
};
const pos = block => block.location;
const same = (row,dim,xyz) => row.dimension === dim
  && Math.floor(row.x) === xyz.x && Math.floor(row.y) === xyz.y
  && Math.floor(row.z) === xyz.z;
function normalize(dim) {
  return dim.startsWith("minecraft:") ? dim : "minecraft:" + dim;
}
function dimensionOf(raw) {
  try { return world.getDimension(raw); }
  catch { return world.getDimension(raw.split(":").pop()); }
}
function identity(block) {
  const xyz=pos(block),dim=normalize(block.dimension.id);
  return read(world,KEY).find(row=>same(row,dim,xyz));
}
function register(block,owner=null) {
  const xyz=pos(block),dim=normalize(block.dimension.id);
  const rows=read(world,KEY);
  let row=rows.find(r=>same(r,dim,xyz));
  if(!row) {
    if(rows.length>=150) throw Error("Limite de 150 Waystones atingido.");
    const id="ws_"+Math.random().toString(36).slice(2)+Date.now().toString(36);
    row={id,name:"Marco "+(rows.length+1),dimension:dim,
      x:xyz.x,y:xyz.y,z:xyz.z,owner};
    rows.push(row);save(world,KEY,rows);
  }
  return row;
}
function deleteRecord(block) {
  const xyz=pos(block),dim=normalize(block.dimension.id);
  const before=read(world,KEY);
  const after=before.filter(row=>!same(row,dim,xyz));
  if(after.length!==before.length) save(world,KEY,after);
}
function present(row) {
  try {
    return dimensionOf(row.dimension).getBlock({
      x:Math.floor(row.x),y:Math.floor(row.y),z:Math.floor(row.z)
    })?.typeId===BLOCK;
  } catch { return false; }
}
function arrival(row) {
  const dim=dimensionOf(row.dimension),base={
    x:Math.floor(row.x),y:Math.floor(row.y),z:Math.floor(row.z)
  };
  if(dim.getBlock(base)?.typeId!==BLOCK) return null;
  for(const [dx,dz] of DIRECTION) {
    const here={x:base.x+dx,y:base.y,z:base.z+dz};
    try {
      const feet=dim.getBlock(here),head=dim.getBlock({...here,y:here.y+1});
      const below=dim.getBlock({...here,y:here.y-1});
      if(feet?.isAir && head?.isAir && below && !below.isAir && !below.isLiquid)
        return {dimension:dim,location:{x:here.x+0.5,y:here.y,z:here.z+0.5}};
    } catch { /* Unloaded position: do not force-load or teleport. */ }
  }
  return null;
}
export function travelTo(player,id) {
  const rows=read(world,KEY),row=rows.find(x=>x.id===id);
  if(!row || !read(player,KNOWN).includes(id)) {
    player.sendMessage("§eDestino removido ou não ativado.");return false;
  }
  const safe=arrival(row);
  if(!safe) {
    player.sendMessage("§eDestino bloqueado ou região descarregada.");return false;
  }
  try {
    player.teleport(safe.location,{dimension:safe.dimension,checkForBlocks:true});
    player.sendMessage("§bTeleportado para "+row.name+".");return true;
  } catch {
    player.sendMessage("§eNão foi possível completar o teleporte.");return false;
  }
}
async function chooseDestination(player,origin) {
  const known=read(player,KNOWN);
  const rows=read(world,KEY).filter(row=>known.includes(row.id)&&row.id!==origin.id);
  if(!rows.length) { player.sendMessage("§eAtive outro marco primeiro.");return; }
  const menu=new ActionFormData().title("Waystones — destinos").body("Marco atual: "+origin.name);
  for(const row of rows) menu.button(row.name+" §7("+row.dimension.split(":").pop()+")");
  const result=await menu.show(player);
  if(result.canceled||result.selection===undefined||!player.isValid)return;
  const picked=rows[result.selection];
  if(picked) travelTo(player,picked.id);
}
async function rename(player,block,row) {
  if(row.owner && row.owner!==player.name) {
    player.sendMessage("§eApenas quem colocou o marco pode renomeá-lo.");return;
  }
  const form=new ModalFormData().title("Renomear Waystone").textField("Nome do destino","Novo nome",{defaultValue:row.name});
  const result=await form.show(player);
  if(result.canceled||!player.isValid)return;
  const title=String(result.formValues?.[0]??"").trim().replace(/[\r\n§]/g,"").slice(0,40);
  if(!title){player.sendMessage("§eNome vazio não permitido.");return;}
  if(block.typeId!==BLOCK)return;
  const rows=read(world,KEY),at=rows.findIndex(x=>x.id===row.id);
  if(at<0||!same(rows[at],normalize(block.dimension.id),pos(block)))return;
  rows[at].name=title;save(world,KEY,rows);
  player.sendMessage("§aMarco renomeado: "+title);
}
async function interact(player,block) {
  const now=system.currentTick;
  if(busy.has(player.id)||now-(recent.get(player.id)??-1000)<5)return;
  busy.add(player.id);recent.set(player.id,now);
  try {
    if(!player.isValid||block.typeId!==BLOCK)return;
    const row=register(block);
    const known=read(player,KNOWN);
    if(!known.includes(row.id)) {
      known.push(row.id);save(player,KNOWN,known);
      try {block.setPermutation(block.permutation.withState("minizin:active",true));}
      catch(error){console.warn("[Waystones] active state: "+String(error));}
      player.sendMessage("§aMarco ativado: "+row.name+".");return;
    }
    const menu=new ActionFormData().title("Waystone — "+row.name)
      .body("Destino atual: "+row.name+" | "+row.dimension)
      .button("Viajar").button("Renomear").button("Cancelar");
    const result=await menu.show(player);
    if(result.canceled||result.selection===undefined||!player.isValid)return;
    if(result.selection===0)await chooseDestination(player,row);
    if(result.selection===1)await rename(player,block,row);
  } catch(error){player.sendMessage("§cWaystones: "+String(error));}
  finally {busy.delete(player.id);}
}
// Component API v2, registered in early execution. Only this block responds.
system.beforeEvents.startup.subscribe(init=>{
  init.blockComponentRegistry.registerCustomComponent("minizin:waystone_control",{
    onPlace: e=>system.run(()=>{
      try{if(e.block.typeId===BLOCK)register(e.block);}
      catch(error){console.warn("[Waystones] place: "+String(error));}
    }),
    onPlayerInteract:e=>{
      if(e.player)system.run(()=>interact(e.player,e.block));
    },
    onPlayerBreak:e=>{
      // A destroyed block cannot be read reliably here; its location remains.
      system.run(()=>{
        try {deleteRecord(e.block);}
        catch(error){console.warn("[Waystones] break: "+String(error));}
      });
    }
  });
});
// Independent safeguard, for API versions with a different break lifecycle.
world.afterEvents.playerBreakBlock.subscribe(e=>{
  if(e.brokenBlockPermutation.type.id!==BLOCK)return;
  try{deleteRecord(e.block);}catch(error){console.warn("[Waystones] cleanup: "+String(error));}
});
world.afterEvents.playerLeave.subscribe(({playerId})=>{busy.delete(playerId);recent.delete(playerId);});
// Legacy entity migration is deliberately bounded to loaded chunks by players.
// Never overwrite another block and never delete an unconverted legacy marker.
function migrate(marker) {
  const loc=marker.location,xyz={x:Math.floor(loc.x),y:Math.floor(loc.y),z:Math.floor(loc.z)};
  const block=marker.dimension.getBlock(xyz);
  if(!block?.isAir)return false;
  let id=marker.getDynamicProperty(LEGACY_ID);
  const rows=read(world,KEY);
  if(typeof id!=="string") {
    const old=rows.find(row=>same(row,normalize(marker.dimension.id),xyz));
    id=old?.id??"ws_"+Math.random().toString(36).slice(2)+Date.now().toString(36);
  }
  const at=rows.findIndex(row=>row.id===id);
  const row={id,name:at>=0?rows[at].name:"Marco migrado",dimension:normalize(marker.dimension.id),
    x:xyz.x,y:xyz.y,z:xyz.z,owner:at>=0?rows[at].owner??null:null};
  if(at>=0)rows[at]=row;else rows.push(row);
  // Record must be durable before removing the legacy entity.
  save(world,KEY,rows);
  block.setType(BLOCK);
  marker.remove();
  return true;
}
system.runInterval(()=>{
  const visited=new Set();
  for(const player of world.getAllPlayers()) {
    try {
      const markers=player.dimension.getEntities({type:LEGACY,location:player.location,maxDistance:24});
      for(const marker of markers){
        if(visited.has(marker.id))continue;visited.add(marker.id);
        try {migrate(marker);}
        catch(error){console.warn("[Waystones] preserve legacy marker: "+String(error));}
      }
    }catch(error){console.warn("[Waystones] migration: "+String(error));}
  }
},80);
