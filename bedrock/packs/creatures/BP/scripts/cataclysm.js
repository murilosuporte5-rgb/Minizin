import {get,put,state,hp,playerTarget,nearby,hit,cone,distance,eventSound} from "./core.js";
import {ignisPhase} from "./math.js";
const TYPE="minizin_creatures:ignis";
function begin(e,attack,ticks){put(e,"ignis_move",attack);put(e,"ignis_time",ticks);state(e,"attack",attack);}
export function tickIgnis(e,tick){
  if(e.typeId!==TYPE)return;
  const health=hp(e),phase=Number(get(e,"ignis_phase",0)),desired=ignisPhase(health.now,health.max);
  const time=Number(get(e,"ignis_time",0)),move=get(e,"ignis_move","idle");
  if(time>0) {
    const left=Math.max(0,time-10);put(e,"ignis_time",left);
    if(move==="phase2"&&time>=40&&left<40){put(e,"ignis_phase",1);state(e,"phase",1);}
    if(move==="phase3"&&time>=70&&left<70){put(e,"ignis_phase",2);state(e,"phase",2);}
    if(move==="shield_smash"&&time>=30&&left<30){for(const x of nearby(e,8))hit(e,x,12,1.2);eventSound(e,"mob.irongolem.walk");}
    if(move==="soul_sweep"&&time>=30&&left<30){const target=playerTarget(e,12);if(target)cone(e,target,80,12,15,1);}
    if(move==="ultimate"&&time>=40&&left<40){for(const x of nearby(e,14)){hit(e,x,20,2);try{x.setOnFire(6);}catch{}}}
    if(left===0)state(e,"attack","idle");
    return;
  }
  if(desired>phase){begin(e,desired===1?"phase2":"phase3",desired===1?68:120);return;}
  if(tick%40!==0)return;
  const target=playerTarget(e,20);if(!target)return;
  const d=distance(e.location,target.location);
  if(phase===2 && Number(get(e,"ultimate_cd",0))<=tick && d<=15){
    put(e,"ultimate_cd",tick+1200);begin(e,"ultimate",114);
  } else if(phase>=1&&d<=12)begin(e,"soul_sweep",58);
  else if(d<=8)begin(e,"shield_smash",70);
}
