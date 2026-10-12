import {get,put,state,playerTarget,nearby,hp,hit,distance,direction,eventSound} from "./core.js";
const TYPE="minizin_creatures:ender_guardian";
// Source: Ender_Guardian_Entity.java: 50% helmet phase; 48/83-tick stomp,
// 62-tick black hole, 75-tick mass destruction, 200/280/400/600-tick cooldowns.
function animate(e,move,ticks){put(e,"move",move);put(e,"attack_ticks",ticks);state(e,"attack",move);}
function horizontal(e,target){
  const v=direction(e.location,target.location);
  try{target.applyKnockback({x:v.x,z:v.z},1,0.6);}catch{}
}
export function tickEnderGuardian(e,tick){
  if(e.typeId!==TYPE)return;
  const life=hp(e),rage=life.now<=life.max/2;
  if(rage&&!get(e,"helmetless",false)){
    put(e,"helmetless",true);state(e,"helmetless",true);
    animate(e,"mass_destruction",75);put(e,"used_mass",true);return;
  }
  const left=Number(get(e,"attack_ticks",0)),move=get(e,"move","idle");
  const target=playerTarget(e,32);
  if(left>0){
    const next=Math.max(0,left-10);put(e,"attack_ticks",next);
    if((move==="stomp"||move==="rage_stomp")&&left>=20&&next<20){
      for(const x of nearby(e,rage?13:10))hit(e,x,rage?15:10,1.25);
      eventSound(e,"minizin_creatures.ender.stomp");
    }
    if(move==="blackhole"&&target&&left>=20&&left<=60){
      for(const x of nearby(e,14)){
        const v=direction(x.location,e.location);
        try{x.applyImpulse({x:v.x*0.1,y:0.04,z:v.z*0.1});}catch{}
      }
      if(next<20)for(const x of nearby(e,5))hit(e,x,8,0.7);
    }
    if(move==="uppercut"&&target&&left>=30&&next<30){
      for(const x of nearby(e,5)){hit(e,x,11,0.5);horizontal(e,x);}
    }
    if(move==="burst"&&left>=20&&next<20){
      for(const x of nearby(e,6))hit(e,x,12,1.3);
    }
    if(move==="mass_destruction"&&left>=20&&next<20){
      for(const x of nearby(e,18))hit(e,x,23,2);
      eventSound(e,"minizin_creatures.ender.stomp");
    }
    if(move==="rocket_punch"&&target&&left>=20&&next<20){
      for(const x of nearby(e,14))if(distance(x.location,target.location)<=3)hit(e,x,15,1.5);
    }
    if(next===0)state(e,"attack","idle");
    return;
  }
  if(!target||tick%40!==0)return;
  const d=distance(e.location,target.location);
  if(rage&&d>=16&&d<=32&&tick>=Number(get(e,"air_next",0))){
    put(e,"air_next",tick+600);animate(e,"air_strike",123);
  }else if(d>=6&&d<=32&&tick>=Number(get(e,"vortex_next",0))){
    put(e,"vortex_next",tick+280);animate(e,"blackhole",62);
  }else if(d>6&&d<13&&tick>=Number(get(e,"stomp_next",0))){
    put(e,"stomp_next",tick+400);animate(e,rage?"rage_stomp":"stomp",rage?83:48);
  }else if(d<4&&tick>=Number(get(e,"uppercut_next",0))){
    put(e,"uppercut_next",tick+200);animate(e,"uppercut",rage?120:100);
  }else if(d<3)animate(e,"burst",53);
  else if(d<14)animate(e,"rocket_punch",58);
}
