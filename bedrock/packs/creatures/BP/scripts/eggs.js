import {ItemStack} from "@minecraft/server";
import {world,system,get,put,item,take,eventSound,hp} from "./core.js";
// Ported environmental gates from DragonType.updateEggCondition (Java).
// Ice's frozen tile is represented by an egg entity state, not the Java block entity.
const KINDS=["fire","ice","lightning"];
const HATCH_TICKS=7200;
function weather(dim){
  try{return String(dim.getWeather()).toLowerCase();}catch{return String(get(world,"weather_overworld","clear"));}
}
function skyVisible(dim,pos){
  try {const top=dim.getTopmostBlock({x:Math.floor(pos.x),z:Math.floor(pos.z)});return !top||top.y<pos.y;} catch{return false;}
}
function fireNear(dim,pos){
  for(const [x,y,z] of [[0,0,0],[0,-1,0],[1,0,0],[-1,0,0],[0,0,1],[0,0,-1]]){
    try{const id=dim.getBlock({x:Math.floor(pos.x+x),y:Math.floor(pos.y+y),z:Math.floor(pos.z+z)})?.typeId;
      if(id==="minecraft:fire"||id==="minecraft:soul_fire"||id==="minecraft:campfire")return true;}catch{}
  }
  return false;
}
function eggType(e){return e.typeId.match(/^minizin_creatures:(fire|ice|lightning)_dragon_egg$/)?.[1];}
function hatch(e,kind){
  const owner=get(e,"owner","");
  const baby=e.dimension.spawnEntity("minizin_creatures:"+kind+"_dragon",{...e.location,y:e.location.y+1});
  if(owner)put(baby,"owner",owner);
  put(baby,"days",0);put(baby,"age_ticks",0);
  eventSound(e,"random.levelup");
  e.remove();
}
export function tickEgg(e) {
  const kind=eggType(e);if(!kind)return;
  const dim=e.dimension,pos=e.location;
  let eligible=false, frozen=Boolean(get(e,"frozen",false));
  if(kind==="fire")eligible=fireNear(dim,pos);
  if(kind==="lightning")eligible=skyVisible(dim,pos)&&/rain|thunder/.test(weather(dim));
  if(kind==="ice"){
    if(!frozen){
      const block=dim.getBlock({x:Math.floor(pos.x),y:Math.floor(pos.y),z:Math.floor(pos.z)});
      if(block?.typeId==="minecraft:water"&&Math.random()<0.002){
        put(e,"frozen",true);frozen=true;eventSound(e,"random.glass");
      }
    }
    eligible=frozen;
  }
  if(!eligible)return;
  const next=Number(get(e,"incubation",0))+20;
  put(e,"incubation",next);
  if(next>HATCH_TICKS)hatch(e,kind);
}
export function installEggs(){
  world.afterEvents.itemUse.subscribe(ev=>{
    const name=ev.itemStack?.typeId??"";
    const kind=name.match(/^minizin_creatures:dragon_egg_(fire|ice|lightning)$/)?.[1];
    if(!kind)return;
    system.run(()=>{
      const p=ev.source;if(!p.isValid)return;
      const facing=p.getViewDirection(),pos=p.location;
      const egg=p.dimension.spawnEntity("minizin_creatures:"+kind+"_dragon_egg",{
        x:Math.floor(pos.x+facing.x*2)+0.5,y:Math.floor(pos.y),z:Math.floor(pos.z+facing.z*2)+0.5
      });
      put(egg,"owner",p.id);put(egg,"incubation",0);
      take(p,name);
      p.sendMessage("Ovo "+kind+" colocado; incubação condicionada ao ambiente.");
    });
  });
  world.afterEvents.entityDie.subscribe(ev=>{
    const e=ev.deadEntity,kind=e.typeId.match(/^minizin_creatures:(fire|ice|lightning)_dragon$/)?.[1];
    if(!kind)return;
    const age=Number(get(e,"days",0));
    if(age<75)return; // matches adult-only loot gate in original.
    try{e.dimension.spawnItem(new ItemStack("minizin_creatures:dragon_scale_"+kind,1),e.location);}catch(err){console.warn("[Minizin creatures] drop "+err);}
  });
  world.afterEvents.weatherChange.subscribe(ev=>{
    if(ev.dimension!=="minecraft:overworld"&&ev.dimension!=="overworld")return;
    try{put(world,"weather_overworld",String(ev.newWeather));}catch{}
  });
}
