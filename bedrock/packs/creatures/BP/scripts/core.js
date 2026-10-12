import {world,system} from "@minecraft/server";
import {distance,direction,nearSegment} from "./math.js";
export {world,system,distance,direction,nearSegment};
export const PREFIX="minizin_creatures:";
export function get(entity,key,fallback=0) { try {return entity.getDynamicProperty(PREFIX+key)??fallback;} catch {return fallback;} }
export function put(entity,key,value) { entity.setDynamicProperty(PREFIX+key,value); }
export function state(entity,key,value) { try {entity.setProperty(PREFIX+key,value);} catch {} }
export function hp(entity) {const c=entity.getComponent("minecraft:health");return {now:c?.currentValue??0,max:c?.effectiveMax??c?.defaultValue??1};}
export function nearby(entity,radius) {
  const owner=get(entity,"owner","");
  const mounted=new Set((entity.getComponent("minecraft:rideable")?.getRiders()??[]).map(x=>x.id));
  const leader=get(entity,"summoner","");
  return entity.dimension.getEntities({location:entity.location,maxDistance:radius}).filter(x=>x.id!==entity.id&&x.id!==owner&&!mounted.has(x.id)&&x.hasComponent("minecraft:health")&&!(x.typeId.startsWith("minizin_creatures:")&&x.typeId.endsWith("_dragon"))
    &&get(x,"summoner","")!==entity.id&&(!leader||x.id!==leader)&&(!leader||get(x,"summoner","")!==leader));
}
export function playerTarget(entity,radius,ownerId) {
  const ps=entity.dimension.getPlayers({location:entity.location,maxDistance:radius}).filter(p=>p.id!==ownerId&&p.getGameMode?.()!=="Creative"&&p.getGameMode?.()!=="Spectator");
  ps.sort((a,b)=>distance(a.location,entity.location)-distance(b.location,entity.location));
  return ps[0];
}
export function hit(entity,target,amount,push=0) {
  if(!target?.isValid || target.id===entity.id) return;
  target.applyDamage(amount);
  if(push>0) {
    const v=direction(entity.location,target.location);
    try {target.applyKnockback({x:v.x,z:v.z},push,push*0.25);} catch {}
  }
}
export function cone(entity,target,radius,range,amount,knock=0) {
  const aim=direction(entity.location,target.location);
  for(const x of nearby(entity,range)) {
    const d=distance(entity.location,x.location);
    if(d>range||d<0.01)continue;
    const v=direction(entity.location,x.location);
    if(aim.x*v.x+aim.z*v.z>=Math.cos(radius*Math.PI/180)) hit(entity,x,amount,knock);
  }
}
export function rider(entity) {try{return entity.getComponent("minecraft:rideable")?.getRiders()?.find(x=>x.typeId==="minecraft:player");}catch{return undefined;}}
export function item(player) {try{return player.getComponent("minecraft:inventory").container?.getItem(player.selectedSlotIndex)?.typeId;}catch{return undefined;}}
export function take(player,type) {
  if(player.getGameMode?.()==="Creative")return true;
  const inv=player.getComponent("minecraft:inventory")?.container;const i=player.selectedSlotIndex;const s=inv?.getItem(i);
  if(!s||s.typeId!==type)return false;
  if(s.amount===1)inv.setItem(i,undefined);else {s.amount-=1;inv.setItem(i,s);}
  return true;
}
export function eventSound(entity,id) {try{entity.dimension.playSound(id,entity.location);}catch{}}
export function safeLoop(fn) {
  for(const name of ["overworld","nether","the_end"]) {
    let dim;try{dim=world.getDimension(name);}catch{continue;}
    for(const e of dim.getEntities({families:["minizin_creatures"]})) {
      try{fn(e);}catch(err){if(system.currentTick%600===0)console.warn("[Minizin creatures] "+e.typeId+": "+err);}
    }
  }
}
