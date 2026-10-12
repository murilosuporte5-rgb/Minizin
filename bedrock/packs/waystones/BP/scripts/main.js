import { world, system } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";

// Minizin Waystones prototype. Server authoritative: no client-selected coordinates.
// Persisted per world and per player; markers are summonable entities, not blocks.
const KEY="minizin:waystones_world_v1",KNOWN="minizin:waystones_known_v1",IDENT="minizin:waystone_id";
function read(holder,key){try{const x=holder.getDynamicProperty(key);return typeof x==="string"?JSON.parse(x):[]}catch{return[];}}
function save(holder,key,value){holder.setDynamicProperty(key,JSON.stringify(value));}
function asDimension(raw){try{return world.getDimension(raw);}catch{return world.getDimension(raw.split(":").pop());}}
function getId(marker){
 let id=marker.getDynamicProperty(IDENT);
 if(typeof id!=="string"){
  id="ws_"+Math.random().toString(36).slice(2)+Date.now().toString(36);
  marker.setDynamicProperty(IDENT,id);
 }
 return id;
}
function register(marker){
 const id=getId(marker),list=read(world,KEY),l=marker.location,d=marker.dimension.id;
 const row={id,name:"Marco "+(list.length+1),dimension:d,x:l.x,y:l.y,z:l.z};
 const index=list.findIndex(x=>x.id===id);
 if(index<0){
  if(list.length>=150)throw Error("Limit of 150 Waystones reached");
  list.push(row);
 }else list[index]={...list[index],x:l.x,y:l.y,z:l.z,dimension:d};
 save(world,KEY,list);
 return list.find(x=>x.id===id);
}
async function interact(player,marker){
 const here=register(marker),known=read(player,KNOWN);
 if(!known.includes(here.id)){
  known.push(here.id);save(player,KNOWN,known);
  player.sendMessage("§aMarco ativado: "+here.name+"! Toque novamente para viajar.");
  return;
 }
 const all=read(world,KEY).filter(x=>known.includes(x.id)&&x.id!==here.id);
 if(!all.length){player.sendMessage("§eAtive outro marco antes de viajar.");return;}
 const form=new ActionFormData().title("Minizin • Waystones").body("Escolha um marco já ativado:");
 for(const x of all)form.button(x.name+" §7("+x.dimension+")");
 const result=await form.show(player);
 if(result.canceled||result.selection===undefined)return;
 const dest=all[result.selection];if(!dest)return;
 // Recheck server-side authorization and destination after the async dialog.
 if(!read(player,KNOWN).includes(dest.id))return;
 const serverRecord=read(world,KEY).find(x=>x.id===dest.id);
 if(!serverRecord)return;
 try{
  const dim=asDimension(serverRecord.dimension);
  player.teleport({x:serverRecord.x+1.5,y:serverRecord.y+0.5,z:serverRecord.z+0.5},{dimension:dim});
  player.sendMessage("§bTeleportado para "+serverRecord.name+".");
 }catch(error){player.sendMessage("§cNão foi possível carregar o destino: "+String(error));}
}
world.afterEvents.playerInteractWithEntity.subscribe(ev=>{
 if(ev.target.typeId!=="minizin:andesite_waystone")return;
 system.run(()=>{interact(ev.player,ev.target).catch(e=>ev.player.sendMessage("§cWaystones: "+e));});
});
