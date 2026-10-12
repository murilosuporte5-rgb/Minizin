import {world,system} from "@minecraft/server";
import {held,tell} from "./core.js";

// Entity carry keeps the real entity (inventory, custom name, health, AI).
const MOBS=new Set(["minecraft:cow","minecraft:sheep","minecraft:pig",
  "minecraft:chicken","minecraft:goat","minecraft:villager","minecraft:villager_v2"]);
const BLOCKS=new Set(["minecraft:chest","minecraft:trapped_chest","minecraft:barrel",
  "minecraft:furnace","minecraft:blast_furnace","minecraft:smoker","minecraft:stone",
  "minecraft:cobblestone","minecraft:oak_planks","minecraft:crafting_table",
  "minecraft:bookshelf","minecraft:oak_log","minecraft:dirt","minecraft:grass_block",
  "minecraft:deepslate","minecraft:anvil","minecraft:iron_block"]);
const STORAGE="minizin:carry_block_v2";
const carrying=new Map(),locks=new Set();
const FACE={Up:[0,1,0],Down:[0,-1,0],North:[0,0,-1],
  South:[0,0,1],East:[1,0,0],West:[-1,0,0]};
const distance=(a,b)=>{
  const x=a.location,y=b.location;
  return Math.hypot(x.x-y.x,x.y-y.y,x.z-y.z);
};
function state(player) {
  try {
    const raw=player.getDynamicProperty(STORAGE);
    return typeof raw==="string"?JSON.parse(raw):null;
  }catch{return null;}
}
function save(player,value) {
  player.setDynamicProperty(STORAGE,value?JSON.stringify(value):undefined);
}
function manager(){return world.structureManager;}
function sameDimension(a,b){return a===b||a.split(":").pop()===b.split(":").pop();}
function sameBlock(dim,at,type){
  try{return world.getDimension(dim).getBlock(at)?.typeId===type;}
  catch{return false;}
}
function adjacentChest(block){
  if(!block.typeId.includes("chest"))return false;
  const p=block.location;
  for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1]]){
    const other=block.dimension.getBlock({x:p.x+dx,y:p.y,z:p.z+dz});
    if(other?.typeId===block.typeId)return true;
  }
  return false;
}
export function release(player){
  const previous=carrying.get(player.id);
  if(!previous)return false;
  carrying.delete(player.id);
  tell(player,"Entidade original solta sem recriação.");
  return true;
}
export function pickedBlock(player){
  return state(player)?.type??null;
}
function grab(player,position,dimensionId){
  const block=player.dimension.getBlock(position);
  if(!block||!BLOCKS.has(block.typeId)) {
    tell(player,"Este bloco não está na lista de tipos transportáveis.");return;
  }
  if(distance(player,block)>5)return;
  if(adjacentChest(block)){tell(player,"Separe o baú duplo antes de transportar.");return;}
  const existing=state(player);
  if(existing){tell(player,"Você já está transportando um bloco.");return;}
  if(carrying.has(player.id)){tell(player,"Solte a criatura antes de pegar um bloco.");return;}
  const type=block.typeId,p=block.location;
  const id="minizin:carry_"+Date.now().toString(36)+"_"+Math.random().toString(36).slice(2,12);
  try{
    manager().createFromWorld(id,block.dimension,p,p,{includeBlocks:true,includeEntities:false});
    // The structure remains durable in the world until a confirmed placement.
    save(player,{id,type,origin:{...p},originDimension:dimensionId,stage:"held"});
    try{block.setType("minecraft:air");}
    catch(error){save(player,null);manager().delete(id);throw error;}
    tell(player,"Transportando "+type+". Agache e toque com graveto no local de destino.");
  }catch(error){tell(player,"Captura recusada: "+String(error));}
}
function finalize(player,carried){
  // Only forget the cargo after checking actual block placement.
  save(player,null);
  try{manager().delete(carried.id);}
  catch(error){console.warn("[CarryOn] cleanup "+String(error));}
}
function put(player,base,face){
  const cargo=state(player);if(!cargo)return;
  if(cargo.stage==="placing") {
    tell(player,"Colocação em andamento; o estado será reconciliado.");return;
  }
  const off=FACE[face];
  if(!off){tell(player,"Face do bloco desconhecida.");return;}
  // Crash recovery: if the original block remains, do not create a duplicate.
  if(sameBlock(cargo.originDimension,cargo.origin,cargo.type)){
    save(player,null);
    try{manager().delete(cargo.id);}catch{}
    tell(player,"Captura não concluída: o bloco original ainda existe.");return;
  }
  const dest={x:base.x+off[0],y:base.y+off[1],z:base.z+off[2]};
  let target;
  try{target=player.dimension.getBlock(dest);}
  catch{tell(player,"Área do destino descarregada.");return;}
  if(!target?.isAir){tell(player,"Espaço de destino ocupado.");return;}
  if(!manager().get(cargo.id)){tell(player,"Estrutura não encontrada; carga preservada para inspeção.");return;}
  const pending={...cargo,stage:"placing",target:dest,targetDimension:player.dimension.id};
  try {
    save(player,pending);
    manager().place(cargo.id,player.dimension,dest,{includeBlocks:true,includeEntities:false});
    system.runTimeout(()=>{
      if(!player.isValid)return;
      try {
        const current=state(player);
        if(current?.id!==cargo.id||current.stage!=="placing")return;
        if(sameBlock(player.dimension.id,dest,cargo.type)){
          finalize(player,cargo);tell(player,"Bloco real colocado; conteúdo preservado na estrutura.");
        }else {
          save(player,{...cargo,stage:"held"});
          tell(player,"Colocação não confirmada. A carga continua disponível.");
        }
      } catch(error){tell(player,"Erro na verificação: "+String(error));}
    },2);
  }catch(error){
    save(player,{...cargo,stage:"held"});
    tell(player,"Não foi possível colocar: "+String(error));
  }
}
export function installCarryOn(){
  world.beforeEvents.playerInteractWithBlock.subscribe(e=>{
    if(e.isFirstEvent===false||!e.player.isSneaking||e.itemStack?.typeId!=="minecraft:stick")return;
    const {player}=e,pos={...e.block.location},dim=e.block.dimension.id,face=e.blockFace;
    if(!state(player)&&!BLOCKS.has(e.block.typeId))return;
    e.cancel=true;
    system.run(()=>{
      if(locks.has(player.id))return;
      locks.add(player.id);
      try{if(state(player))put(player,pos,face);else grab(player,pos,dim);}
      finally{locks.delete(player.id);}
    });
  });
  world.afterEvents.playerInteractWithEntity.subscribe(e=>{
    if(!e.player.isSneaking||!MOBS.has(e.target.typeId))return;
    const hand=e.beforeItemStack??e.itemStack??held(e.player);
    if(hand?.typeId!=="minecraft:stick")return;
    system.run(()=>{
      const p=e.player,t=e.target;
      try {
        if(carrying.has(p.id)){release(p);return;}
        if(state(p)||distance(p,t)>5)return;
        for(const value of carrying.values())if(value.entity.id===t.id){
          tell(p,"Esta criatura já está sendo transportada.");return;
        }
        carrying.set(p.id,{player:p,entity:t,dimension:t.dimension.id});
        tell(p,"Criatura original em transporte. !minizin soltar para liberar.");
      }catch(error){tell(p,"Entidade não transportada: "+String(error));}
    });
  });
  system.runInterval(()=>{
    for(const [id,entry] of carrying){
      try {
        const {player,entity,dimension}=entry;
        if(!player.isValid||!entity.isValid||!sameDimension(player.dimension.id,dimension)){
          carrying.delete(id);continue;
        }
        const d=player.getViewDirection(),p=player.location;
        entity.teleport({x:p.x+d.x*1.7,y:p.y+0.4,z:p.z+d.z*1.7},
          {dimension:player.dimension,keepVelocity:false});
      }catch(error){carrying.delete(id);console.warn("[CarryOn] "+String(error));}
    }
  },8);
  world.afterEvents.playerSpawn.subscribe(e=>{
    if(!e.initialSpawn)return;
    const cargo=state(e.player);
    if(cargo?.stage!=="placing")return;
    system.runTimeout(()=>{
      if(!e.player.isValid)return;
      if(sameBlock(cargo.targetDimension,cargo.target,cargo.type))
        finalize(e.player,cargo);
      else save(e.player,{...cargo,stage:"held"});
    },30);
  });
  world.afterEvents.playerLeave.subscribe(e=>{carrying.delete(e.playerId);locks.delete(e.playerId);});
}
export function carriedCount(){return carrying.size;}
