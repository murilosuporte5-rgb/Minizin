import {world,system} from "@minecraft/server";
import {held,tell} from "./core.js";
const ALLOWED=new Set(["minecraft:cow","minecraft:sheep","minecraft:pig","minecraft:chicken"]);
const carrying=new Map(); // player.id -> {player, entity}; no entity clone, NBT destruction or block pickup
function distance(a,b){const d=a.location,e=b.location;return Math.hypot(d.x-e.x,d.y-e.y,d.z-e.z);}
function isHoldingAnother(targetId){
  for(const item of carrying.values())if(item.entity.id===targetId)return true;
  return false;
}
export function release(player){
  if(!carrying.delete(player.id))return false;
  tell(player,"Animal solto. A entidade original foi preservada.");
  return true;
}
export function installCarryOn(){
  world.afterEvents.playerInteractWithEntity.subscribe(e=>{
    if(!e.player.isSneaking||!ALLOWED.has(e.target.typeId))return;
    const hand=e.beforeItemStack??e.itemStack??held(e.player);
    if(hand?.typeId!=="minecraft:stick")return;
    system.run(()=>{
      const player=e.player,target=e.target;
      if(carrying.has(player.id)){release(player);return;}
      try{
        if(distance(player,target)>5)return;
        if(isHoldingAnother(target.id)){tell(player,"Este animal já está sendo carregado.");return;}
        carrying.set(player.id,{player,entity:target,dimension:target.dimension.id});
        tell(player,"Carregando animal original. Para soltar: !minizin soltar.");
      }catch(err){tell(player,"Falha ao pegar: "+String(err));}
    });
  });
  // A few teleport calls per second; never kills/spawns mobs or writes their inventory.
  system.runInterval(()=>{
    for(const [id,data] of carrying){
      try{
        const {player,entity,dimension}=data;
        if(!player.isValid||!entity.isValid||player.dimension.id!==dimension){
          carrying.delete(id);continue;
        }
        const direction=player.getViewDirection(),p=player.location;
        const target={x:p.x+direction.x*1.8,y:p.y+0.35,z:p.z+direction.z*1.8};
        entity.teleport(target,{dimension:player.dimension,keepVelocity:false});
      }catch(err){carrying.delete(id);console.warn("[Minizin CarryOn] ",String(err));}
    }
  },8);
  world.afterEvents.playerLeave.subscribe(e=>{carrying.delete(e.playerId);});
}
export function carriedCount(){return carrying.size;}
