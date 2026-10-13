/* Aether equipment, v0.3.0 candidate.
 * Java reference: AetherAccessorySlots (Accessories API).
 * Bedrock has no public API for adding native inventory tabs, so the same
 * category/count contract is persisted in a server-ui accessory menu. The
 * native offhand is only a one-time migration path for old prototype worlds.
 */
import {world,system,ItemStack,EquipmentSlot,EnchantmentTypes} from "@minecraft/server";
import {ActionFormData} from "@minecraft/server-ui";
import {EQUIPMENT} from "./aether_equipment_catalog.js";
const SLOT_KEY="minizin:aether_accessories_v2",LEGACY_SLOT_KEY="minizin:aether_accessories_v1";
const SLOTS=[
  {id:"ring",label:"Anéis",count:2},
  {id:"pendant",label:"Pendants",count:1},
  {id:"gloves",label:"Luvas",count:1},
  {id:"cape",label:"Capas",count:1},
  {id:"shield",label:"Escudo",count:1},
  {id:"accessory",label:"Acessórios",count:2}
];
const COUNT=SLOTS.reduce((sum,slot)=>sum+slot.count,0);
const busy=new Set(),timers=new Map();
const inventory=p=>p.getComponent("minecraft:inventory")?.container;
const accessory=id=>Boolean(EQUIPMENT[id]?.accessory);
function slotIndex(category,ordinal){
  let offset=0;
  for(const slot of SLOTS){if(slot.id===category)return offset+ordinal;offset+=slot.count;}
  return -1;
}
function slotFor(index){
  let offset=0;
  for(const slot of SLOTS){if(index<offset+slot.count)return {slot,ordinal:index-offset};offset+=slot.count;}
  return undefined;
}
function emptySlots(){return Array(COUNT).fill(null);}
function read(p){
  const value=p.getDynamicProperty(SLOT_KEY);
  if(value!==undefined){
    let rows;
    try{rows=typeof value==="string"?JSON.parse(value):null;}
    catch{throw Error("Dados dos acessórios inválidos; preservados para recuperação.");}
    if(!Array.isArray(rows)||rows.length!==COUNT)
      throw Error("Slots dos acessórios inválidos; dados preservados para recuperação.");
    return rows;
  }
  try{
    const legacy=p.getDynamicProperty(LEGACY_SLOT_KEY),rows=typeof legacy==="string"?JSON.parse(legacy):null;
    if(Array.isArray(rows)&&rows.length===2)return [rows[0]||null,rows[1]||null,...emptySlots().slice(2)];
  }catch{}
  return emptySlots();
}
function write(p,rows){
  if(!Array.isArray(rows)||rows.length!==COUNT)throw Error("Slots inválidos");
  const raw=JSON.stringify(rows);if(raw.length>12000)throw Error("Limite de acessórios");
  p.setDynamicProperty(SLOT_KEY,raw);
}
function serialize(item){
  if(!EQUIPMENT[item?.typeId]?.accessory)throw Error("Somente acessórios do Aether");
  const props={};for(const key of item.getDynamicPropertyIds())props[key]=item.getDynamicProperty(key);
  return {type:item.typeId,name:item.nameTag,lore:item.getLore(),damage:item.getComponent("minecraft:durability")?.damage,
    enchantments:item.getComponent("minecraft:enchantable")?.getEnchantments().map(x=>({id:x.type.id,level:x.level}))||[],props};
}
function deserialize(data){
  if(!EQUIPMENT[data.type]?.accessory)throw Error("Acessório inválido");
  const item=new ItemStack(data.type,1);if(data.name!==undefined)item.nameTag=data.name;item.setLore(data.lore||[]);
  const durability=item.getComponent("minecraft:durability");if(durability&&data.damage!==undefined)durability.damage=data.damage;
  const enchantable=item.getComponent("minecraft:enchantable");
  if((data.enchantments||[]).length){
    if(!enchantable)throw Error("Acessório encantado sem componente de encantamento.");
    enchantable.addEnchantments(data.enchantments.map(entry=>{
      const type=EnchantmentTypes.get(entry.id);
      if(!type)throw Error("Encantamento desconhecido: "+entry.id);
      return {type,level:entry.level};
    }));
  }
  for(const [key,value] of Object.entries(data.props||{}))item.setDynamicProperty(key,value);
  return item;
}
function label(slot){return slot?.name||slot?.type?.split(":").pop()?.replace(/_/g," ")||"Vazio";}
async function menu(player){
  if(busy.has(player.id))return;busy.add(player.id);
  try{
    const rows=read(player),form=new ActionFormData().title("Aether • acessórios")
      .body("Slots Java do Aether, independentes da mão secundária. Segure o item e toque no slot correspondente.");
    for(let index=0;index<COUNT;index++){const ref=slotFor(index);form.button(ref.slot.label+" "+(ref.ordinal+1)+": "+label(rows[index]));}
    const response=await form.show(player);if(response.canceled||response.selection===undefined||!player.isValid)return;
    const index=response.selection,ref=slotFor(index),inv=inventory(player),heldSlot=player.selectedSlotIndex;if(!ref||!inv)return;
    const held=inv.getItem(heldSlot),fresh=read(player);
    if(JSON.stringify(fresh)!==JSON.stringify(rows)){player.sendMessage("§eOs acessórios mudaram. Abra novamente.");return;}
    if(held&&EQUIPMENT[held.typeId]?.accessory){
      const expected=EQUIPMENT[held.typeId].slot;
      if(expected!==ref.slot.id){player.sendMessage("§eEste item pertence ao slot de "+(SLOTS.find(x=>x.id===expected)?.label||"outro tipo")+".");return;}
      const next=[...fresh],replacement=next[index]?deserialize(next[index]):undefined;next[index]=serialize(held);
      try{inv.setItem(heldSlot,replacement);write(player,next);}catch(error){inv.setItem(heldSlot,held);throw error;}
      player.sendMessage("§a[Aether] "+ref.slot.label+" equipado no espaço "+(ref.ordinal+1)+".");
    }else if(!held&&fresh[index]){
      const restored=deserialize(fresh[index]),next=[...fresh];next[index]=null;
      try{inv.setItem(heldSlot,restored);write(player,next);}catch(error){inv.setItem(heldSlot,undefined);throw error;}
      player.sendMessage("§a[Aether] "+ref.slot.label+" retirado do espaço "+(ref.ordinal+1)+".");
    }else player.sendMessage("§eSegure um acessório do Aether para equipar, ou deixe a mão vazia para retirar.");
  }catch(error){player.sendMessage("§c[Aether] "+String(error));}finally{busy.delete(player.id);}
}
world.beforeEvents.playerInteractWithBlock.subscribe(event=>{
  if(event.isFirstEvent===false)return;const held=event.itemStack;
  if(!EQUIPMENT[held?.typeId]?.accessory&&!(event.player.isSneaking&&!held))return;
  event.cancel=true;system.run(()=>menu(event.player));
});
world.afterEvents.itemUse.subscribe(({source,itemStack})=>{if(EQUIPMENT[itemStack?.typeId]?.accessory)system.run(()=>menu(source));});
function wear(player,amount){
  if(String(player.getGameMode?.()).toLowerCase()==="creative")return;
  const inv=inventory(player),slot=player.selectedSlotIndex,item=inv?.getItem(slot);
  if(!EQUIPMENT[item?.typeId]||EQUIPMENT[item.typeId].accessory)return;
  const durability=item.getComponent("minecraft:durability");if(!durability)return;
  if(durability.damage+amount>=durability.maxDurability)inv.setItem(slot,undefined);else{durability.damage+=amount;inv.setItem(slot,item);}
}
world.afterEvents.entityHitEntity.subscribe(({damagingEntity,hitEntity:target})=>{
  if(damagingEntity.typeId!=="minecraft:player")return;const player=damagingEntity,item=inventory(player)?.getItem(player.selectedSlotIndex),spec=EQUIPMENT[item?.typeId];
  if(!spec||spec.accessory)return;
  try{
    if(system.currentTick-(timers.get(player.id)??-1000)>=12){timers.set(player.id,system.currentTick);
      if(spec.power==="flaming"){const enchant=item.getComponent("minecraft:enchantable")?.getEnchantment("fire_aspect");target.setOnFire(30+(enchant?.level||0)*4,true);}
      else if(spec.power==="vampire"){const health=player.getComponent("minecraft:health");if(health)health.setCurrentValue(Math.min(health.effectiveMax,health.currentValue+1));}}
    wear(player,1);
  }catch(error){console.warn("[Aether tools] "+String(error));}
});
world.afterEvents.playerBreakBlock.subscribe(({player,itemStackBeforeBreak})=>{if(EQUIPMENT[itemStackBeforeBreak?.typeId]&&!EQUIPMENT[itemStackBeforeBreak.typeId].accessory)wear(player,1);});
system.runInterval(()=>{
  for(const player of world.getAllPlayers())try{
    let rows=read(player);const equipment=player.getComponent("minecraft:equippable"),offhand=equipment?.getEquipment(EquipmentSlot.Offhand);
    // Migrate rings/accessories from the old offhand prototype exactly once.
    if(offhand&&EQUIPMENT[offhand.typeId]?.accessory&&rows.every(value=>!value)){
      const category=EQUIPMENT[offhand.typeId].slot,position=slotIndex(category,0);
      if(position>=0){rows[position]=serialize(offhand);equipment.setEquipment(EquipmentSlot.Offhand,undefined);write(player,rows);player.sendMessage("§b[Aether] Acessório migrado para o slot "+(SLOTS.find(x=>x.id===category)?.label||category)+".");}
    }
    const mode=String(player.getGameMode?.()).toLowerCase();
    if(mode!=="spectator"&&!player.isFlying){
      const iceIndex=rows.findIndex(value=>value?.type==="minizin_aether:ice_ring"||value?.type==="minizin_aether:ice_pendant");
      if(iceIndex>=0){const location=player.location;let frozen=0;
        for(let dx=-1;dx<=1;dx++)for(let dz=-1;dz<=1;dz++){const block=player.dimension.getBlock({x:Math.floor(location.x)+dx,y:Math.floor(location.y)-1,z:Math.floor(location.z)+dz});if(block?.typeId==="minecraft:water"&&block.permutation.getState("liquid_depth")===0){block.setType("minecraft:frosted_ice");frozen++;}}
        if(frozen&&mode!=="creative"){const item=deserialize(rows[iceIndex]),durability=item.getComponent("minecraft:durability");if(durability){const next=durability.damage+Math.ceil(frozen/3),after=[...rows];after[iceIndex]=next>=durability.maxDurability?null:(durability.damage=next,serialize(item));write(player,after);rows=after;}}
      }
    }
    const equipped=rows.filter(Boolean).map(value=>value.type);
    if(equipped.includes("minizin_aether:invisibility_cloak"))player.addEffect?.("invisibility",20,{amplifier:0,showParticles:false});
    if(equipped.includes("minizin_aether:golden_feather")||equipped.includes("minizin_aether:agility_cape")||equipped.includes("minizin_aether:valkyrie_cape"))player.addEffect?.("slow_falling",20,{amplifier:0,showParticles:false});
    if(equipped.includes("minizin_aether:iron_bubble"))player.addEffect?.("water_breathing",20,{amplifier:0,showParticles:false});
    if(equipped.includes("minizin_aether:regeneration_stone"))player.addEffect?.("regeneration",20,{amplifier:0,showParticles:false});
  }catch(error){console.warn("[Aether accessories] "+String(error));}
},10);
world.afterEvents.playerLeave.subscribe(({playerId})=>{busy.delete(playerId);timers.delete(playerId);});
