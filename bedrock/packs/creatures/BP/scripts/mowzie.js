import {world,system,get,put,state,playerTarget,nearby,distance,direction,nearSegment,hit,eventSound} from "./core.js";
// Hooks the existing Mowzie Bluff from bedrock/packs/mowzie, without editing its RP/geometry.
const TYPE="minizin:bluff";
export function tickBluff(e,tick){
  if(e.typeId!==TYPE)return;
  const phase=get(e,"bluff_phase","idle");
  const timer=Number(get(e,"bluff_timer",0));
  if(phase==="idle"){
    if(tick%50!==0)return;
    const p=playerTarget(e,12);
    if(!p||distance(e.location,p.location)<6)return;
    put(e,"bluff_phase","startup");put(e,"bluff_timer",11);
    put(e,"bluff_target_x",p.location.x);put(e,"bluff_target_z",p.location.z);
    eventSound(e,"mob.irongolem.throw");
    return;
  }
  if(timer>1){put(e,"bluff_timer",timer-1);return;}
  if(phase==="startup"){
    put(e,"bluff_phase","fall");put(e,"bluff_timer",18);
    e.applyImpulse({x:0,y:-0.8,z:0});return;
  }
  if(phase==="fall"){
    if(!e.isOnGround && timer>1){put(e,"bluff_timer",timer-1);e.applyImpulse({x:0,y:-0.3,z:0});return;}
    const from=e.location,to={x:Number(get(e,"bluff_target_x",from.x)),y:from.y,z:Number(get(e,"bluff_target_z",from.z))};
    for(const x of nearby(e,15)){
      if(nearSegment(x.location,from,to,1.1))hit(e,x,18,0.8);
    }
    put(e,"bluff_phase","recovery");put(e,"bluff_timer",34);
    eventSound(e,"mob.irongolem.walk");return;
  }
  put(e,"bluff_phase","idle");put(e,"bluff_timer",0);
}
export function installMowzie(){
  // Original entity is maintained by the separate mowzie pack. No duplicate models or scripts.
  system.runInterval(()=>{
    for(const d of ["overworld","nether","the_end"]){
      let dim;try{dim=world.getDimension(d);}catch{continue;}
      for(const e of dim.getEntities({type:TYPE}))try{tickBluff(e,system.currentTick);}catch(err){if(system.currentTick%600===0)console.warn("[Bluff] "+err);}
    }
  },1);
}
