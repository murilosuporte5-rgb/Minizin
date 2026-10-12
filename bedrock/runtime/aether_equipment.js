import {world,system,EquipmentSlot,EntityDamageCause} from '@minecraft/server';
import {EQUIPMENT} from './aether_equipment_catalog.js';
const timers=new Map();
function inventory(p){return p.getComponent('minecraft:inventory')?.container;}
function wear(p,amount){
  if(typeof p.getGameMode==='function'&&String(p.getGameMode()).toLowerCase()==='creative')return;
  const inv=inventory(p),slot=p.selectedSlotIndex,item=inv?.getItem(slot);
  if(!item||!EQUIPMENT[item.typeId])return;
  const durability=item.getComponent('minecraft:durability');if(!durability)return;
  const next=durability.damage+amount;
  if(next>=durability.maxDurability)inv.setItem(slot,undefined);else{durability.damage=next;inv.setItem(slot,item);}
}
world.afterEvents.entityHitEntity.subscribe(({damagingEntity,hitEntity:target})=>{
  if(damagingEntity.typeId!=='minecraft:player')return;
  const p=/** @type {import('@minecraft/server').Player} */(damagingEntity);
  const item=inventory(p)?.getItem(p.selectedSlotIndex),spec=EQUIPMENT[item?.typeId];
  if(!spec)return;
  try{
    wear(p,1);
    if(system.currentTick-(timers.get(p.id)??-1000)<12)return;
    timers.set(p.id,system.currentTick);
    if(spec.power==='flaming'){
      const enchant=item.getComponent('minecraft:enchantable')?.getEnchantment('fire_aspect');
      target.setOnFire(30+(enchant?.level??0)*4,true);
    }else if(spec.power==='vampire'){
      const health=p.getComponent('minecraft:health');
      health.setCurrentValue(Math.min(health.effectiveMax,health.currentValue+1));
    }
  }catch(error){console.warn('[Aether equipment]',String(error));}
});
world.afterEvents.playerBreakBlock.subscribe(({player,itemStackBeforeBreak})=>{
  if(EQUIPMENT[itemStackBeforeBreak?.typeId])wear(player,1);
});
world.beforeEvents.playerInteractWithBlock.subscribe(e=>{
  if(!EQUIPMENT[e.itemStack?.typeId]?.ring||e.isFirstEvent===false)return;
  e.cancel=true;system.run(()=>{
    const inv=inventory(e.player),slot=e.player.selectedSlotIndex,item=inv?.getItem(slot);
    if(item?.typeId!==e.itemStack.typeId)return;
    const equipment=e.player.getComponent('minecraft:equippable'),old=equipment.getEquipment(EquipmentSlot.Offhand);
    if(equipment.setEquipment(EquipmentSlot.Offhand,item)){
      inv.setItem(slot,old);e.player.sendMessage('§b[Aether]§r Anel equipado na mão secundária.');
    }
  });
});
system.runInterval(()=>{
  for(const player of world.getAllPlayers()){
    try{
      const equipped=player.getComponent('minecraft:equippable').getEquipment(EquipmentSlot.Offhand);
      if(equipped?.typeId!=='minizin_aether:ice_ring')continue;
      const mode=String(player.getGameMode()).toLowerCase();
      if(mode==='spectator'||player.isFlying)continue;
      const p=player.location;let frozen=0;
      for(let x=-1;x<=1;x++)for(let z=-1;z<=1;z++){
        const block=player.dimension.getBlock({x:Math.floor(p.x)+x,y:Math.floor(p.y)-1,z:Math.floor(p.z)+z});
        if(block?.typeId==='minecraft:water'&&block.permutation.getState('liquid_depth')===0){block.setType('minecraft:frosted_ice');frozen++;}
      }
      const durability=equipped.getComponent('minecraft:durability');
      if(frozen&&durability&&mode!=='creative'){const next=durability.damage+Math.ceil(frozen/3);
        if(next<durability.maxDurability)durability.damage=next;
        player.getComponent('minecraft:equippable').setEquipment(EquipmentSlot.Offhand,
          next>=durability.maxDurability?undefined:equipped);}
    }catch(error){console.warn('[Aether ice ring]',String(error));}
  }
},10);
world.afterEvents.playerLeave.subscribe(({playerId})=>timers.delete(playerId));
