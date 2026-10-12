import {get,put,state,playerTarget,nearby,hp,hit,cone,distance,nearSegment,eventSound} from "./core.js";
const BOSS="minizin_creatures:umvuthi",MINION="minizin_creatures:umvuthana";
function start(e,name,duration){put(e,"umvuthi_action",name);put(e,"umvuthi_ticks",duration);state(e,"attack",name);}
function summon(e){
  const minions=e.dimension.getEntities({type:MINION,location:e.location,maxDistance:42})
    .filter(x=>get(x,"summoner","")===e.id);
  if(minions.length>=4)return;
  for(let i=0;i<Math.min(2,4-minions.length);i++){
    const angle=2*Math.PI*i/3+Math.random();
    const loc={x:e.location.x+Math.cos(angle)*3,y:e.location.y+0.3,z:e.location.z+Math.sin(angle)*3};
    const child=e.dimension.spawnEntity(MINION,loc);
    put(child,"summoner",e.id);put(child,"life",2400);
  }
}
export function tickUmvuthi(e,tick){
  if(e.typeId===MINION){
    let remaining=Number(get(e,"life",2400))-10;
    if(remaining<=0){e.remove();return;}
    put(e,"life",remaining);
    const target=playerTarget(e,12),left=Number(get(e,"umvuthi_ticks",0));
    if(left>0){
      const next=Math.max(0,left-10);put(e,"umvuthi_ticks",next);
      if(left>10&&next<=10&&target)cone(e,target,45,3.5,3,0.45);
      if(next===0)state(e,"attack","idle");
      return;
    }
    if(target&&distance(e.location,target.location)<=4&&tick%60===0){
      start(e,tick%120===0?"attack_slash_left":"attack_slash_right",30);
    }
    return;
  }
  if(e.typeId!==BOSS)return;
  const life=hp(e),target=playerTarget(e,30),move=get(e,"umvuthi_action","idle"),left=Number(get(e,"umvuthi_ticks",0));
  if(left>0){
    const next=Math.max(0,left-10);put(e,"umvuthi_ticks",next);
    if(move==="sun_strike"&&left>20&&next<=20&&target){
      const pos=target.location;
      for(const victim of nearby(e,30))if(distance(victim.location,pos)<3.2)hit(e,victim,8,0.8);
    }
    if(move==="solar_beam"&&left>=40&&next<40&&target){
      for(const victim of nearby(e,28))if(nearSegment(victim.location,e.location,target.location,1.4))hit(e,victim,14,1.1);
    }
    if(move==="flare"&&left>=20&&next<20)for(const victim of nearby(e,7))hit(e,victim,5,1.1);
    if(move==="supernova"&&left>=20&&next<20){
      for(const victim of nearby(e,10.5))hit(e,victim,19,2);
      eventSound(e,"minizin_creatures.umvuthi.supernova");
    }
    if(move==="spawn_strix"&&left>=20&&next<20)summon(e);
    if(next===0)state(e,"attack","idle");
    return;
  }
  if(!target||tick%40!==0)return;
  const d=distance(e.location,target.location);
  const minions=e.dimension.getEntities({type:MINION,location:e.location,maxDistance:40})
    .filter(x=>get(x,"summoner","")===e.id).length;
  if(life.now<=life.max*0.6&&d<10.5&&tick>=Number(get(e,"nova_next",0))){
    put(e,"nova_next",tick+230);start(e,"supernova",100);
    eventSound(e,"minizin_creatures.umvuthi.supernova_start");
  }else if(minions<2&&d>5.5&&tick>=Number(get(e,"summon_next",0))){
    put(e,"summon_next",tick+360);start(e,"spawn_strix",60);
  }else if(d<=6)start(e,"flare",32);
  else if(d<22&&tick>=Number(get(e,"beam_next",0))){
    put(e,"beam_next",tick+230);start(e,"solar_beam",120);
  }else if(d<30)start(e,"sun_strike",50);
}
