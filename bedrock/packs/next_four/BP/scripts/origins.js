import {world,system,ItemStack,EnchantmentTypes} from "@minecraft/server";
import {ActionFormData} from "@minecraft/server-ui";
import {ORIGINS_CATALOG,IMPLEMENTED_PASSIVES} from "./catalog.js";
import {tell} from "./core.js";
const KEY="minizin:origin_v1";
const busy=new Set();
const inventoryBusy=new Set();
const cooldown=new Map();
const SHULK_KEY="minizin:origins_shulk_inventory_v1";
const SHULK_SLOTS=9;
const SHULK_MAX_BYTES=24000;
const FIRE_CAUSES=new Set(["fire","fireTick","lava","campfire","soulCampfire","hotFloor"]);
const SOLID_FOR_CLIMB=new Set([
  "minecraft:stone","minecraft:cobblestone","minecraft:deepslate","minecraft:cobbled_deepslate",
  "minecraft:brick_block","minecraft:bricks","minecraft:oak_planks","minecraft:birch_planks",
  "minecraft:spruce_planks","minecraft:jungle_planks","minecraft:acacia_planks","minecraft:dark_oak_planks",
  "minecraft:netherrack","minecraft:end_stone","minecraft:iron_block","minecraft:gold_block",
  "minecraft:diamond_block","minecraft:obsidian"
]);
function originOf(player){
  const id=player.getDynamicProperty(KEY);
  return typeof id==="string"?id:null;
}
function inWater(player){return Boolean(player.isInWater||player.isInWaterOrRain);
}
function adjacentSolid(player){
  const p=player.location;
  for(const [x,z] of [[1,0],[-1,0],[0,1],[0,-1]]){
    try{
      const block=player.dimension.getBlock({x:Math.floor(p.x+x),y:Math.floor(p.y),z:Math.floor(p.z+z)});
      if(block&&!block.isAir&&(SOLID_FOR_CLIMB.has(block.typeId)||block.typeId.startsWith("minecraft:")))return true;
    }catch{}
  }
  return false;
}
function parseShulk(player){
  const raw=player.getDynamicProperty(SHULK_KEY);
  if(raw===undefined)return Array(SHULK_SLOTS).fill(null);
  const rows=JSON.parse(raw);
  if(!Array.isArray(rows)||rows.length!==SHULK_SLOTS)throw Error("Inventário Shulk corrompido; dados preservados para inspeção.");
  return rows;
}
function writeShulk(player,rows){
  if(!Array.isArray(rows)||rows.length!==SHULK_SLOTS)throw Error("Quantidade inválida de espaços Shulk.");
  const raw=JSON.stringify(rows);
  if(raw.length>SHULK_MAX_BYTES)throw Error("Os metadados excedem o limite seguro do inventário Shulk.");
  player.setDynamicProperty(SHULK_KEY,raw);
}
function encodeShulkItem(item){
  if(!item?.typeId)throw Error("Item ausente.");
  if(item.typeId.endsWith("shulker_box")||item.typeId==="minecraft:bundle"||item.getComponent?.("minecraft:storage_item"))
    throw Error("Contêineres aninhados não são permitidos no inventário Shulk.");
  const props={};for(const key of item.getDynamicPropertyIds?.()||[])props[key]=item.getDynamicProperty(key);
  const enchantable=item.getComponent?.("minecraft:enchantable");
  const data={type:item.typeId,amount:item.amount,lore:item.getLore?.()||[],
    damage:item.getComponent?.("minecraft:durability")?.damage,
    enchantments:enchantable?.getEnchantments?.().map(x=>({id:x.type.id,level:x.level}))||[],
    props};
  if(item.nameTag!==undefined)data.name=item.nameTag;
  try{data.keep=item.keepOnDeath;data.lock=item.lockMode;data.destroy=item.getCanDestroy?.()||[];data.place=item.getCanPlaceOn?.()||[];}catch{}
  return data;
}
function decodeShulkItem(data){
  if(!data?.type||!Number.isInteger(data.amount)||data.amount<1)throw Error("Item armazenado inválido.");
  const item=new ItemStack(data.type,data.amount);
  if(data.name!==undefined)item.nameTag=data.name;
  item.setLore(data.lore||[]);
  if(data.keep!==undefined)item.keepOnDeath=Boolean(data.keep);
  if(data.lock!==undefined)try{item.lockMode=data.lock;}catch{}
  try{item.setCanDestroy(data.destroy||[]);item.setCanPlaceOn(data.place||[]);}catch{}
  const durability=item.getComponent?.("minecraft:durability");
  if(durability&&data.damage!==undefined)durability.damage=data.damage;
  const enchantable=item.getComponent?.("minecraft:enchantable");
  if(enchantable&&(data.enchantments||[]).length){
    enchantable.addEnchantments(data.enchantments.map(x=>({type:EnchantmentTypes.get(x.id),level:x.level})));
  }
  for(const [key,value] of Object.entries(data.props||{}))item.setDynamicProperty(key,value);
  return item;
}
function shulkLabel(row,index){
  if(!row)return "Espaço "+(index+1)+": vazio";
  return "Espaço "+(index+1)+": "+(row.name||row.type.split(":").pop().replace(/_/g," "))+" x"+row.amount;
}
export async function openShulkInventory(player){
  if(originOf(player)!=="shulk"){tell(player,"O inventário Shulk exige a origem Shulk.");return;}
  if(inventoryBusy.has(player.id))return;
  inventoryBusy.add(player.id);
  try{
    const rows=parseShulk(player),form=new ActionFormData().title("Origins • Inventário Shulk")
      .body("9 espaços persistentes do poder Java shulker_inventory. Segure um item para trocar com o espaço; deixe a mão vazia para retirar.");
    rows.forEach((row,index)=>form.button(shulkLabel(row,index)));
    const response=await form.show(player);
    if(response.canceled||response.selection===undefined||!player.isValid)return;
    const index=response.selection,inv=player.getComponent("minecraft:inventory")?.container;
    if(!inv)throw Error("Inventário do jogador indisponível.");
    const fresh=parseShulk(player);if(JSON.stringify(fresh)!==JSON.stringify(rows))throw Error("Inventário Shulk mudou; abra novamente para evitar perda.");
    const held=inv.getItem(player.selectedSlotIndex),stored=fresh[index];
    if(!held&&!stored){tell(player,"Este espaço já está vazio.");return;}
    const replacement=stored?decodeShulkItem(stored):undefined;
    const next=[...fresh];
    if(held)next[index]=encodeShulkItem(held);else next[index]=null;
    try{
      inv.setItem(player.selectedSlotIndex,replacement);
      writeShulk(player,next);
    }catch(error){inv.setItem(player.selectedSlotIndex,held);throw error;}
    tell(player,held?"Item guardado no espaço Shulk; o item anterior foi colocado na mão.":"Item retirado do espaço Shulk.");
  }catch(error){tell(player,"Inventário Shulk: "+String(error));}
  finally{inventoryBusy.delete(player.id);}
}
/** @param {import('@minecraft/server').Player} player */
export function activateOrigin(player){
  const id=player.getDynamicProperty(KEY),now=system.currentTick;
  const abilityCooldown=id==="enderian"?30:200;
  if(now-(cooldown.get(player.id)??-1000)<abilityCooldown){tell(player,"Poder recarregando ("+(abilityCooldown/20)+"s).");return;}
  if(id==="elytrian"){
    player.applyImpulse({x:0,y:1.2,z:0});
    cooldown.set(player.id,now);tell(player,"Impulso aéreo ativado.");return;
  }
  if(id==="enderian"){
    // Java's throw_ender_pearl is a projectile power, not a direct teleport.
    // Use the native Bedrock projectile so collision, landing and damage stay
    // owned by the engine instead of fabricating a destination search.
    const direction=player.getViewDirection?.()??{x:0,y:0,z:1};
    const base=player.getHeadLocation?.()??{x:player.location.x,y:player.location.y+1.5,z:player.location.z};
    try{
      const pearl=player.dimension.spawnEntity("minecraft:ender_pearl",base);
      pearl.applyImpulse({x:direction.x*1.5,y:direction.y*1.5,z:direction.z*1.5});
      cooldown.set(player.id,now);tell(player,"Pérola do Ender lançada.");
    }catch(error){tell(player,"Não foi possível lançar a Pérola do Ender: "+String(error));}
    return;
  }
  if(id==="arachnid"){
    if(player.isSneaking&&adjacentSolid(player)){
      try{player.applyImpulse({x:0,y:0.16,z:0});cooldown.set(player.id,now);tell(player,"Escalada ativada enquanto agachado.");return;}
      catch(error){tell(player,"Falha na escalada: "+String(error));return;}
    }
    try {
      const hit=player.getBlockFromViewDirection({maxDistance:8});
      if(!hit){tell(player,"Mire em um bloco próximo para produzir a teia.");return;}
      const base=hit.block.location;
      const pos={x:base.x,y:base.y+1,z:base.z};
      const target=player.dimension.getBlock(pos);
      if(!target?.isAir){tell(player,"Não há espaço livre acima do bloco.");return;}
      target.setType("minecraft:web");
      cooldown.set(player.id,now);
      const dim=player.dimension;
      system.runTimeout(()=>{
        try{const current=dim.getBlock(pos);if(current?.typeId==="minecraft:web")current.setType("minecraft:air");}
        catch(error){console.warn("[Minizin Origins] web cleanup "+String(error));}
      },200);
      tell(player,"Teia real criada por 10 segundos.");return;
    }catch(error){tell(player,"Falha ao criar teia: "+String(error));return;}
  }
  if(id==="phantom"){
    player.addEffect("invisibility",200,{amplifier:0,showParticles:false});
    cooldown.set(player.id,now);
    tell(player,"Invisibilidade por 10 segundos (não permite atravessar blocos).");
    return;
  }
  tell(player,"Esta origem ainda não possui poder ativo implementado.");
}
export async function chooseOrigin(player){
  if(busy.has(player.id))return;
  busy.add(player.id);
  try{
    const prev=player.getDynamicProperty(KEY);
    const form=new ActionFormData().title("Minizin • Origins")
      .body("Escolha sua origem. Os poderes portados aparecem como adaptação verificável; os demais continuam catalogados.\nAtual: "+(prev??"nenhuma"));
    for(const item of ORIGINS_CATALOG){
      const flag=IMPLEMENTED_PASSIVES[item.id]?"[passivo]":item.id==="shulk"?"[parcial]":"[catálogo]";
      form.button(item.label+" "+flag);
    }
    const choice=await form.show(player);
    if(choice.canceled||choice.selection===undefined)return;
    const selected=ORIGINS_CATALOG[choice.selection];
    if(!selected)return;
    player.setDynamicProperty(KEY,selected.id);
    tell(player,"Origem selecionada: "+selected.label+". Use !origins inventario para o poder Shulk quando aplicável.");
  }catch(e){tell(player,"Não foi possível abrir Origins: "+String(e));}
  finally{busy.delete(player.id);}
}
export function installOrigins(){
  world.afterEvents.playerLeave.subscribe(({playerId})=>cooldown.delete(playerId));
  world.beforeEvents.chatSend?.subscribe(ev=>{
    const command=ev.message.trim().toLowerCase();
    if(command!=="!origins inventario"&&command!=="!origins inventário"&&command!=="!origins shulk")return;
    ev.cancel=true;
    system.run(()=>openShulkInventory(ev.sender));
  });
  world.beforeEvents.entityHurt.subscribe(e=>{
    try{
      if(e.hurtEntity.typeId!=="minecraft:player")return;
      const id=originOf(e.hurtEntity),cause=e.damageSource?.cause;
      if(cause==="fall"&&(id==="feline"||id==="avian"))e.cancel=true;
      if(id==="blazeborn"&&FIRE_CAUSES.has(cause))e.cancel=true;
    }catch(error){console.warn("[Minizin Origins] fall immunity: "+String(error));}
  });
  world.afterEvents.entityHitEntity.subscribe(e=>{
    try{
      const attacker=e.damagingEntity,target=e.hitEntity;
      if(attacker?.typeId!=="minecraft:player"||!target?.isValid)return;
      if(originOf(attacker)==="blazeborn"&&attacker.isOnFire)
        target.applyDamage(3);
    }catch(error){console.warn("[Minizin Origins] burning wrath: "+String(error));}
  });
  world.afterEvents.itemUse.subscribe(({source,itemStack})=>{
    if(itemStack.typeId==="minecraft:feather"&&source.isSneaking)system.run(()=>activateOrigin(source));
  });
  world.afterEvents.playerInteractWithBlock.subscribe(({player,itemStack,isFirstEvent})=>{
    if(!player.isSneaking||isFirstEvent===false)return;
    if(itemStack?.typeId==="minecraft:book")system.run(()=>chooseOrigin(player));
    if(itemStack?.typeId==="minecraft:feather")system.run(()=>activateOrigin(player));
  });
  system.runInterval(()=>{
    for(const player of world.getAllPlayers()){
      try{
        const id=player.getDynamicProperty(KEY);
        if(typeof id!=="string")continue;
        const passive=IMPLEMENTED_PASSIVES[id];
        if(passive)player.addEffect(passive.effect,120,{amplifier:0,showParticles:false});
        if(id==="shulk")player.addEffect("resistance",100,{amplifier:0,showParticles:false});
        if(id==="shulk")player.addEffect("haste",100,{amplifier:0,showParticles:false});
        if(id==="merling"){
          player.addEffect("water_breathing",100,{amplifier:0,showParticles:false});
          if(inWater(player)){
            player.addEffect("speed",90,{amplifier:1,showParticles:false});
            player.addEffect("night_vision",100,{amplifier:0,showParticles:false});
          }
        }
        if(id==="avian"&&!player.isOnGround)
          player.addEffect("slow_falling",100,{amplifier:0,showParticles:false});
        if(id==="feline"&&player.isSprinting)
          player.addEffect("jump_boost",100,{amplifier:0,showParticles:false});
        if(id==="elytrian"&&!player.isOnGround)
          player.addEffect("slow_falling",100,{amplifier:0,showParticles:false});
        if(id==="phantom"&&player.isSneaking)
          player.addEffect("invisibility",100,{amplifier:0,showParticles:false});
        if((id==="blazeborn"||id==="enderian")&&inWater(player))
          player.applyDamage(1);
      }catch(e){console.warn("[Minizin Origins] ",String(e));}
    }
  },80);
}
export function currentOrigin(player){
  const id=player.getDynamicProperty(KEY);
  const o=ORIGINS_CATALOG.find(x=>x.id===id);
  const implemented={
    arachnid:"teia real + escalada agachada (adaptada)",
    avian:"queda lenta + imunidade a queda",
    blazeborn:"imunidade ao fogo + dano incendiário + vulnerabilidade à água",
    elytrian:"impulso aéreo + queda lenta (elytra visual ainda não equipado)",
    enderian:"Pérola do Ender real + vulnerabilidade à água",
    feline:"visão noturna + salto de sprint + imunidade a queda",
    merling:"respiração/visão aquática + velocidade na água",
    phantom:"invisibilidade agachado + ativação temporária",
    shulk:"resistência + pressa + inventário persistente de 9 espaços (UI adaptada; sem aba nativa)"
  };
  tell(player,o?"Sua origem: "+o.label+" ("+(implemented[id]??"sem poderes portados")+")":"Nenhuma origem selecionada. Digite !minizin origins.");
}
