import {world, system} from "@minecraft/server";
// Both the item component and itemUse event may fire: de-duplicate by player/item tick.
const handlers=[];
const recent=new Map();
function dispatch(player, typeId){
  if(!player?.isValid||!typeId||!typeId.startsWith("minizin_creatures:"))return;
  const key=player.id+":"+typeId, now=system.currentTick;
  if(now-(recent.get(key)??-100)>3){
    recent.set(key,now);
    for(const handler of handlers){
      try{handler(player,typeId);}catch(error){console.warn("[Minizin controls] "+error);}
    }
  }
}
export function onUse(handler){handlers.push(handler);}
export function installControls(){
  system.beforeEvents.startup.subscribe(event=>{
    event.itemComponentRegistry.registerCustomComponent("minizin_creatures:activate",{
      onUse:ev=>system.run(()=>dispatch(ev.source,ev.itemStack?.typeId)),
      onUseOn:ev=>system.run(()=>dispatch(ev.source,ev.itemStack?.typeId))
    });
  });
  world.afterEvents.itemUse.subscribe(ev=>system.run(()=>dispatch(ev.source,ev.itemStack?.typeId)));
}
