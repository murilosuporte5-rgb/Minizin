import {world,system} from "@minecraft/server";
import {ActionFormData} from "@minecraft/server-ui";
import {tell,hasItem,takeOne,clamp,read,write} from "./core.js";

// Physical power network. These are Minizin energy units, NOT Forge FE interop.
const KEY="minizin:rftools_grid_v2",LEGACY="minizin:rftools_energy_v1";
const GEN="minizin:rftools_generator",CELL="minizin:rftools_cell";
const CABLE="minizin:rftools_cable",LAMP="minizin:rftools_lamp";
const machines=new Set([GEN,CELL,LAMP]),allowed=new Set([GEN,CELL,CABLE,LAMP]);
const delta=[[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]];
const max={[GEN]:400,[CELL]:1000,[LAMP]:0};
const busy=new Set();
const key=(dim,p)=>dim+":"+Math.floor(p.x)+","+Math.floor(p.y)+","+Math.floor(p.z);
function locate(id) {
  const at=id.lastIndexOf(":"),[x,y,z]=id.slice(at+1).split(",").map(Number);
  return {dim:id.slice(0,at),pos:{x,y,z}};
}
function at(dim,loc){try{return dim.getBlock(loc);}catch{return undefined;}}
function load(){return read(world,KEY,{});}
function save(data){
  const payload=JSON.stringify(data);
  if(Object.keys(data).length>256||payload.length>29000)
    throw Error("Limite de 256 máquinas ou 29KB por mundo.");
  world.setDynamicProperty(KEY,payload);
}
function register(block){
  if(!machines.has(block.typeId))return;
  const id=key(block.dimension.id,block.location),db=load();
  if(db[id])return;
  db[id]={type:block.typeId,energy:0};save(db);
}
// BFS follows cables only. Results are actual adjacent devices in loaded chunks.
function linked(block){
  const dim=block.dimension,visited=new Set(),queue=[block.location],found=[];
  const root=key(dim.id,block.location);
  visited.add(root);
  while(queue.length && visited.size<64){
    const current=queue.shift();
    for(const offset of delta){
      const p={x:current.x+offset[0],y:current.y+offset[1],z:current.z+offset[2]};
      const id=key(dim.id,p);
      if(visited.has(id))continue;
      visited.add(id);
      const next=at(dim,p);
      if(!next||!allowed.has(next.typeId))continue;
      if(next.typeId===CABLE)queue.push(p);
      else if(id!==root)found.push({id,type:next.typeId});
    }
  }
  return found;
}
function setLamp(block,powered){
  try{
    if(block.permutation.getState("minizin:lit")!==powered)
      block.setPermutation(block.permutation.withState("minizin:lit",powered));
  }catch(error){console.warn("[Minizin RFTools] light: "+String(error));}
}
function tick(){
  const db=load(),entries=Object.keys(db);
  let changed=false;
  for(const id of entries){
    const row=db[id];if(row?.type!==GEN||row.energy<1)continue;
    const {dim,pos}=locate(id);let dimension;
    try{dimension=world.getDimension(dim);}catch{continue;}
    const block=at(dimension,pos);
    if(!block)continue;
    if(block.typeId!==GEN){delete db[id];changed=true;continue;}
    for(const remote of linked(block)){
      if(remote.type!==CELL||db[remote.id]?.type!==CELL)continue;
      const target=db[remote.id],amount=Math.min(40,row.energy,max[CELL]-target.energy);
      if(amount>0){row.energy-=amount;target.energy+=amount;changed=true;break;}
    }
  }
  for(const id of entries){
    const row=db[id];if(row?.type!==LAMP)continue;
    const {dim,pos}=locate(id);let dimension;
    try{dimension=world.getDimension(dim);}catch{continue;}
    const block=at(dimension,pos);
    if(!block)continue;
    if(block.typeId!==LAMP){delete db[id];changed=true;continue;}
    let powered=false;
    for(const remote of linked(block)){
      if(remote.type!==GEN&&remote.type!==CELL)continue;
      const source=db[remote.id];
      if(source&&source.energy>=2){source.energy-=2;changed=true;powered=true;break;}
    }
    setLamp(block,powered);
  }
  if(changed)try{save(db);}catch(error){console.warn("[RFTools] "+String(error));}
}
async function legacy(player,block){
  const id=key(block.dimension.id,block.location),db=read(world,LEGACY,{});
  const energy=clamp(Number(db[id]??0),0,200);
  const f=new ActionFormData().title("RFTools • magnetita legada")
    .body("Energia: "+energy+"/200").button("Adicionar redstone (+10)")
    .button("Visão noturna (-5)").button("Consultar");
  const r=await f.show(player);
  if(r.canceled||r.selection===undefined||!player.isValid)return;
  if(at(player.dimension,block.location)?.typeId!=="minecraft:lodestone")return;
  const all=read(world,LEGACY,{});
  let now=clamp(Number(all[id]??0),0,200);
  if(r.selection===0){
    if(now>190||!hasItem(player,"minecraft:redstone")||!takeOne(player,"minecraft:redstone"))return;
    now+=10;
  }else if(r.selection===1){
    if(now<5)return;
    player.addEffect("night_vision",400,{amplifier:0,showParticles:false});now-=5;
  }else if(r.selection!==2)return;
  all[id]=now;write(world,LEGACY,all);tell(player,"Energia legada: "+now);
}
async function open(player,block){
  if(busy.has(player.id))return;
  busy.add(player.id);
  try{
    if(block.typeId==="minecraft:lodestone"){await legacy(player,block);return;}
    if(block.typeId===CABLE){tell(player,"Cabo conectando máquinas próximas.");return;}
    if(!machines.has(block.typeId))return;
    register(block);
    const id=key(block.dimension.id,block.location),db=load(),row=db[id];
    const name=block.typeId===GEN?"Gerador":block.typeId===CELL?"Célula":"Lâmpada";
    const menu=new ActionFormData().title("RFTools • "+name)
      .body("Carga: "+row.energy+"/"+max[block.typeId]+
        "\nConexões carregadas: "+linked(block).length);
    if(block.typeId===GEN){
      menu.button("Consumir carvão (+80)").button("Consumir carvão vegetal (+60)");
    }else menu.button("Atualizar conexões");
    const choice=await menu.show(player);
    if(choice.canceled||choice.selection===undefined||!player.isValid)return;
    if(player.dimension.id!==block.dimension.id||at(player.dimension,block.location)?.typeId!==block.typeId)
      throw Error("A máquina foi removida ou ficou distante.");
    if(block.typeId!==GEN){tell(player,"Conexões: "+linked(block).length);return;}
    const fuel=choice.selection===0?"minecraft:coal":"minecraft:charcoal";
    const gain=choice.selection===0?80:60;
    const fresh=load(),g=fresh[id];
    if(!g||g.energy+gain>max[GEN]){tell(player,"Gerador cheio.");return;}
    if(!hasItem(player,fuel)||!takeOne(player,fuel)){tell(player,"Combustível indisponível.");return;}
    g.energy+=gain;save(fresh);
    tell(player,"Gerador carregado: "+g.energy+"/"+max[GEN]);
  }catch(error){tell(player,"RFTools: "+String(error));}
  finally{busy.delete(player.id);}
}
export async function openMachine(player){
  const hit=player.getBlockFromViewDirection({maxDistance:6});
  if(!hit){tell(player,"Olhe para um dispositivo RFTools.");return;}
  await open(player,hit.block);
}
// Automatically registers on import; Next Four's existing main.js stays untouched.
world.afterEvents.playerInteractWithBlock.subscribe(e=>{
  if(e.isFirstEvent===false||!allowed.has(e.block.typeId))return;
  system.run(()=>open(e.player,e.block));
});
world.afterEvents.playerPlaceBlock.subscribe(e=>{
  if(machines.has(e.block.typeId))
    system.run(()=>{try{register(e.block);}catch(err){console.warn(String(err));}});
});
world.afterEvents.playerBreakBlock.subscribe(e=>{
  if(!allowed.has(e.brokenBlockPermutation.type.id))return;
  system.run(()=>{
    const db=load(),id=key(e.block.dimension.id,e.block.location);
    if(db[id]){delete db[id];save(db);}
  });
});
system.runInterval(tick,40);
