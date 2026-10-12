import {world,system,get,put,state,rider,playerTarget,nearby,distance,hit,eventSound,item,take} from "./core.js";
const TYPE="minizin_creatures:atlatitan";
function begin(e,move,duration){put(e,"move",move);put(e,"frames",duration);state(e,"attack",move);}
export function tickAtlatitan(e,tick){
  if(e.typeId!==TYPE)return;
  const frames=Number(get(e,"frames",0)),move=get(e,"move","idle"),pilot=rider(e);
  if(frames>0){
    const remaining=frames-10;put(e,"frames",remaining);
    if(move==="stomp"&&frames>=20&&remaining<20){
      for(const x of nearby(e,15))if(distance(x.location,e.location)>=4)hit(e,x,12,1.2);
      eventSound(e,"minizin_creatures.atlatitan.stomp");
    }
    if(move==="whip"&&frames>=30&&remaining<30){
      for(const x of nearby(e,12))hit(e,x,8,1);
    }
    if(move==="kick"&&frames>=20&&remaining<20){
      for(const x of nearby(e,5))hit(e,x,6.4,1);
    }
    if(remaining<=0)state(e,"attack","idle");
    return;
  }
  if(pilot)return;
  if(tick%40!==0)return;
  const target=playerTarget(e,16);if(!target)return;
  const d=distance(e.location,target.location);
  if(d>8)begin(e,"whip",50);
  else if(d>3)begin(e,"kick",20);
  else begin(e,"stomp",40);
}
export function installAtlatitan(){
  world.afterEvents.playerInteractWithEntity.subscribe(ev=>{
    if(ev.target.typeId!==TYPE)return;
    system.run(()=>{
      const e=ev.target,p=ev.player;if(!e.isValid||!p.isValid)return;
      if((ev.beforeItemStack?.typeId??item(p))==="minizin_creatures:serene_salad"){
        put(e,"rideable_ticks",1200);take(p,"minizin_creatures:serene_salad");
      } else if(Number(get(e,"rideable_ticks",0))>0)try{e.getComponent("minecraft:rideable")?.addRider(p);}catch{}
    });
  });
  world.afterEvents.itemUse.subscribe(ev=>{
    if(ev.itemStack?.typeId!=="minizin_creatures:serene_salad")return;
    system.run(()=>{
      const e=ev.source.getComponent("minecraft:riding")?.entityRidingOn;
      if(e?.typeId===TYPE&&Number(get(e,"frames",0))<=0&&Number(get(e,"meter",1))>=1){
        put(e,"meter",0);begin(e,"stomp",40);
      }
    });
  });
  system.runInterval(()=>{
    for(const dim of ["overworld","nether","the_end"]){
      let d;try{d=world.getDimension(dim);}catch{continue;}
      for(const e of d.getEntities({type:TYPE})){
        const t=Number(get(e,"rideable_ticks",0));if(t>0)put(e,"rideable_ticks",Math.max(0,t-20));
        put(e,"meter",Math.min(1,Number(get(e,"meter",1))+0.05));
      }
    }
  },20);
}
