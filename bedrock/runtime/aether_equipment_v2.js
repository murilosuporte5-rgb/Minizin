/* Aether equipment, v0.2.5 candidate.
 * Two persisted accessory slots, separate from the native offhand.
 * Slots are virtual and displayed through server-ui, NOT native inventory UI.
 * Aether ring behavior is sourced from the original item classes where known.
 */
import {world,system,ItemStack,EnchantmentTypes} from "@minecraft/server";
import {ActionFormData} from "@minecraft/server-ui";
import {EQUIPMENT} from "./aether_equipment_catalog.js";
const SLOT_KEY="minizin:aether_accessories_v1",COUNT=2;
const busy=new Set(),timers=new Map();
const inventory=p=>p.getComponent("minecraft:inventory")?.container;
const ring=id=>EQUIPMENT[id]?.ring===true;
function read(p){
  try{
    const v=p.getDynamicProperty(SLOT_KEY);
    const rows=typeof v==="string"?JSON.parse(v):null;
    return Array.isArray(rows)&&rows.length===COUNT?rows:[null,null];
  }catch{return [null,null];}
}
function write(p,rows){
  if(!Array.isArray(rows)||rows.length!==COUNT)throw Error("Slots inválidos");
  const raw=JSON.stringify(rows);
  if(raw.length>12000)throw Error("Limite de acessórios");
  p.setDynamicProperty(SLOT_KEY,raw);
}
function serialize(item){
  if(!ring(item?.typeId))throw Error("Somente anéis do Aether");
  const props={};
  for(const k of item.getDynamicPropertyIds())props[k]=item.getDynamicProperty(k);
  return {type:item.typeId,name:item.nameTag,lore:item.getLore(),
    damage:item.getComponent("minecraft:durability")?.damage,
    enchantments:item.getComponent("minecraft:enchantable")?.getEnchantments()
      .map(x=>({id:x.type.id,level:x.level}))||[],props};
}
function deserialize(data){
  if(!ring(data.type))throw Error("Acessório inválido");
  const item=new ItemStack(data.type,1);
  if(data.name!==undefined)item.nameTag=data.name;
  item.setLore(data.lore||[]);
  const durability=item.getComponent("minecraft:durability");
  if(durability&&data.damage!==undefined)durability.damage=data.damage;
  const enchant=item.getComponent("minecraft:enchantable");
  if(enchant&&data.enchantments?.length)
    enchant.addEnchantments(data.enchantments.map(e=>{
      const type=EnchantmentTypes.get(e.id);
      if(!type)throw Error("Encantamento indisponível");
      return {type,level:e.level};
    }));
  for(const [k,v] of Object.entries(data.props||{}))item.setDynamicProperty(k,v);
  return item;
}
function label(slot){return slot?.name||slot?.type?.split(":").pop()?.replace(/_/g," ")||"Vazio";}
async function menu(p){
  if(busy.has(p.id))return;busy.add(p.id);
  try{
    const rows=read(p),menu=new ActionFormData().title("Aether • anéis")
      .body("2 espaços de acessórios independentes da mão secundária.");
    for(let i=0;i<COUNT;i++)menu.button("Anel "+(i+1)+": "+label(rows[i]));
    const response=await menu.show(p);
    if(response.canceled||response.selection===undefined||!p.isValid)return;
    const index=response.selection,inv=inventory(p),heldSlot=p.selectedSlotIndex;
    if(index<0||index>=COUNT||!inv)return;
    const held=inv.getItem(heldSlot),fresh=read(p);
    if(JSON.stringify(fresh)!==JSON.stringify(rows)){
      p.sendMessage("§eOs acessórios mudaram. Abra novamente.");return;
    }
    if(held&&ring(held.typeId)){
      // In a single server callback, swap the held ring for the equipped one.
      const next=[...fresh];const replacement=next[index]?deserialize(next[index]):undefined;
      next[index]=serialize(held);
      try{
        inv.setItem(heldSlot,replacement);
        write(p,next);
      }catch(error){inv.setItem(heldSlot,held);throw error;}
      p.sendMessage("§a[Aether] Anel equipado no espaço "+(index+1)+".");
    }else if(!held&&fresh[index]){
      const restored=deserialize(fresh[index]),next=[...fresh];next[index]=null;
      try{
        inv.setItem(heldSlot,restored);
        write(p,next);
      }catch(error){inv.setItem(heldSlot,undefined);throw error;}
      p.sendMessage("§a[Aether] Anel retirado do espaço "+(index+1)+".");
    }else p.sendMessage("§eSegure um anel para equipar, ou deixe a mão vazia para retirar.");
  }catch(error){p.sendMessage("§c[Aether] "+String(error));}
  finally{busy.delete(p.id);}
}
world.beforeEvents.playerInteractWithBlock.subscribe(e=>{
  if(e.isFirstEvent===false)return;
  const held=e.itemStack;
  if(!ring(held?.typeId)&&!(e.player.isSneaking&&!held))return;
  e.cancel=true;system.run(()=>menu(e.player));
});
world.afterEvents.itemUse.subscribe(({source,itemStack})=>{
  if(ring(itemStack?.typeId))system.run(()=>menu(source));
});
function wear(p,amount){
  if(String(p.getGameMode?.()).toLowerCase()==="creative")return;
  const inv=inventory(p),slot=p.selectedSlotIndex,item=inv?.getItem(slot);
  if(!EQUIPMENT[item?.typeId]||EQUIPMENT[item?.typeId]?.ring)return;
  const dur=item.getComponent("minecraft:durability");if(!dur)return;
  if(dur.damage+amount>=dur.maxDurability)inv.setItem(slot,undefined);
  else{dur.damage+=amount;inv.setItem(slot,item);}
}
world.afterEvents.entityHitEntity.subscribe(({damagingEntity,hitEntity:target})=>{
  if(damagingEntity.typeId!=="minecraft:player")return;
  const p=damagingEntity,item=inventory(p)?.getItem(p.selectedSlotIndex);
  const spec=EQUIPMENT[item?.typeId];
  if(!spec||spec.ring)return;
  try{
    if(system.currentTick-(timers.get(p.id)??-1000)>=12){
      timers.set(p.id,system.currentTick);
      if(spec.power==="flaming"){
        const enchant=item.getComponent("minecraft:enchantable")?.getEnchantment("fire_aspect");
        target.setOnFire(30+(enchant?.level||0)*4,true);
      }else if(spec.power==="vampire"){
        const health=p.getComponent("minecraft:health");
        if(health)health.setCurrentValue(Math.min(health.effectiveMax,health.currentValue+1));
      }
    }
    wear(p,1);
  }catch(error){console.warn("[Aether tools] "+String(error));}
});
world.afterEvents.playerBreakBlock.subscribe(({player,itemStackBeforeBreak})=>{
  if(EQUIPMENT[itemStackBeforeBreak?.typeId])wear(player,1);
});
system.runInterval(()=>{
  for(const p of world.getAllPlayers()){
    try{
      const rows=read(p),at=rows.findIndex(x=>x?.type==="minizin_aether:ice_ring");
      if(at<0||p.isFlying||String(p.getGameMode?.()).toLowerCase()==="spectator")continue;
      const loc=p.location;let frozen=0;
      for(let dx=-1;dx<=1;dx++)for(let dz=-1;dz<=1;dz++){
        const block=p.dimension.getBlock({
          x:Math.floor(loc.x)+dx,y:Math.floor(loc.y)-1,z:Math.floor(loc.z)+dz
        });
        if(block?.typeId==="minecraft:water"&&block.permutation.getState("liquid_depth")===0){
          block.setType("minecraft:frosted_ice");frozen++;
        }
      }
      if(!frozen||String(p.getGameMode?.()).toLowerCase()==="creative")continue;
      const item=deserialize(rows[at]),dur=item.getComponent("minecraft:durability");
      if(!dur)continue;
      const next=dur.damage+Math.ceil(frozen/3),after=[...rows];
      if(next>=dur.maxDurability)after[at]=null;
      else{dur.damage=next;after[at]=serialize(item);}
      write(p,after);
    }catch(error){console.warn("[Aether ice ring] "+String(error));}
  }
},10);
world.afterEvents.playerLeave.subscribe(({playerId})=>{
  busy.delete(playerId);timers.delete(playerId);
});
