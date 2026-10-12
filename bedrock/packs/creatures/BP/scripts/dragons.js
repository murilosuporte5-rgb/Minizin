import {world,system,get,put,state,rider,item,take,playerTarget,nearby,distance,direction,hit,cone,eventSound} from "./core.js";
import {dragonStage} from "./math.js";
const IDS=["fire_dragon","ice_dragon","lightning_dragon"];
const TYPES=IDS.map(x=>"minizin_creatures:"+x);
const DAY_TICKS=24000;
function stage(e){return dragonStage(Number(get(e,"days",0)));}
function own(e,p){return get(e,"owner","")===p.id;}
function combat(e,target,tick){
  const mode=e.typeId.split(":")[1]; const count=Number(get(e,"cooldown",0));
  if(count>0){put(e,"cooldown",Math.max(0,count-10));return;}
  if(distance(e.location,target.location)<6){
    const attack=Math.floor(tick/50)%3;
    if(attack===0){state(e,"attack","bite");cone(e,target,40,5,7+stage(e)*2,0.3);put(e,"cooldown",30);}
    else if(attack===1){state(e,"attack","tail");for(const x of nearby(e,5))hit(e,x,5+stage(e),0.7);put(e,"cooldown",50);}
    else{state(e,"attack","wing");for(const x of nearby(e,7))hit(e,x,3+stage(e),1.4);put(e,"cooldown",70);}
    return;
  }
  if(distance(e.location,target.location)>22)return;
  state(e,"attack",mode==="lightning_dragon"?"charge":"stream");
  const aim=direction(e.location,target.location);
  for(const x of nearby(e,22)){
    const vec=direction(e.location,x.location);
    if(aim.x*vec.x+aim.z*vec.z<0.94)continue;
    hit(e,x,mode==="lightning_dragon"?13:5+stage(e));
    if(mode==="fire_dragon")try{x.setOnFire(4);}catch{}
    if(mode==="ice_dragon")try{x.addEffect("minecraft:slowness",70,{amplifier:2});}catch{}
    if(mode==="lightning_dragon")try{x.addEffect("minecraft:weakness",80,{amplifier:1});}catch{}
  }
  eventSound(e,"minizin_creatures."+mode.replace("_","." )+"_breath");
  put(e,"cooldown",mode==="lightning_dragon"?100:50);
}
export function tickDragons(e,tick){
  if(!TYPES.includes(e.typeId))return;
  const age=Number(get(e,"age_ticks",0))+10;
  if(age>=DAY_TICKS){put(e,"days",Number(get(e,"days",0))+1);put(e,"age_ticks",age-DAY_TICKS);}
  else put(e,"age_ticks",age);
  const level=stage(e);state(e,"stage",level);
  const pilot=rider(e);
  if(pilot&&level>=3&&own(e,pilot)){
    if(get(e,"flight",false)){
      const v=pilot.getViewDirection();
      e.applyImpulse({x:v.x*0.13,y:Math.max(-0.07,Math.min(0.15,v.y*0.18)),z:v.z*0.13});
    }
    return;
  }
  if(tick%20!==0)return;
  const enemy=playerTarget(e,26,get(e,"owner",""));
  if(enemy&&(!get(e,"owner","")||get(e,"aggressive",false)))combat(e,enemy,tick);
  else state(e,"attack","idle");
}
export function installDragons(){
  world.afterEvents.playerInteractWithEntity.subscribe(ev=>{
    const e=ev.target,p=ev.player;if(!TYPES.includes(e.typeId))return;
    system.run(()=>{
      if(!e.isValid||!p.isValid)return;
      const hand=ev.beforeItemStack?.typeId??item(p);
      if(hand==="minizin_creatures:creative_dragon_meal"&&!get(e,"owner","")){
        put(e,"owner",p.id);p.sendMessage("Dragão domesticado.");take(p,hand);return;
      }
      if(!own(e,p))return;
      if(hand==="minizin_creatures:dragon_meal"){
        put(e,"days",Number(get(e,"days",0))+1);take(p,hand);p.sendMessage("Idade: "+get(e,"days")+" dias / estágio "+stage(e));return;
      }
      if(hand==="minizin_creatures:dragon_armor_iron"){
        put(e,"armor",Math.min(4,Number(get(e,"armor",0))+1));take(p,hand);p.sendMessage("Armadura equipada: "+get(e,"armor")+"/4");return;
      }
      if(!hand&&stage(e)>=3) {
        try {e.getComponent("minecraft:rideable")?.addRider(p);}catch{}
      }
    });
  });
  world.afterEvents.itemUse.subscribe(ev=>{
    const p=ev.source,id=ev.itemStack?.typeId;
    if(!["minizin_creatures:dragon_flute"].includes(id))return;
    system.run(()=>{
      const e=p.getComponent("minecraft:riding")?.entityRidingOn;
      if(!e||!TYPES.includes(e.typeId)||!own(e,p))return;
      if(p.isSneaking){
        const fly=!get(e,"flight",false);put(e,"flight",fly);
        try{e.triggerEvent(fly?"minizin_creatures:fly":"minizin_creatures:land");}catch{}
        p.sendMessage(fly?"Voo habilitado. Direcione a câmera para subir/descer.":"Pouso ativado.");
      } else{
        const target=playerTarget(e,24,p.id);if(target)combat(e,target,system.currentTick);
      }
    });
  });
}
