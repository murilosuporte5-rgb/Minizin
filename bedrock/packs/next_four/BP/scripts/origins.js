import {world,system} from "@minecraft/server";
import {ActionFormData} from "@minecraft/server-ui";
import {ORIGINS_CATALOG,IMPLEMENTED_PASSIVES} from "./catalog.js";
import {tell} from "./core.js";
const KEY="minizin:origin_v1";
const busy=new Set();
const cooldown=new Map();
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
/** @param {import('@minecraft/server').Player} player */
export function activateOrigin(player){
  const id=player.getDynamicProperty(KEY),now=system.currentTick;
  if(now-(cooldown.get(player.id)??-1000)<200){tell(player,"Poder recarregando (10s).");return;}
  if(id==="elytrian"){
    player.applyImpulse({x:0,y:1.2,z:0});
    cooldown.set(player.id,now);tell(player,"Impulso aéreo ativado.");return;
  }
  if(id==="enderian"){
    const direction=player.getViewDirection(),start=player.getHeadLocation();
    const hit=player.dimension.getBlockFromRay(start,direction,{maxDistance:12});
    const limit=hit?Math.max(0,Math.hypot(hit.block.location.x-start.x,hit.block.location.y-start.y,hit.block.location.z-start.z)-1):12;
    for(let d=Math.floor(limit);d>=2;d--){
      const at={x:Math.floor(start.x+direction.x*d)+0.5,y:Math.floor(start.y+direction.y*d),z:Math.floor(start.z+direction.z*d)+0.5};
      try{
        const feet=player.dimension.getBlock(at),head=player.dimension.getBlock({...at,y:at.y+1}),floor=player.dimension.getBlock({...at,y:at.y-1});
        const safeFloor=new Set(['minecraft:stone','minecraft:dirt','minecraft:grass_block','minecraft:cobblestone',
          'minecraft:deepslate','minecraft:cobbled_deepslate','minecraft:bedrock','minecraft:netherrack','minecraft:end_stone',
          'minecraft:oak_planks','minecraft:birch_planks','minecraft:spruce_planks','minecraft:sandstone','minecraft:bricks']);
        if(!feet?.isAir||!head?.isAir||!safeFloor.has(floor?.typeId))continue;
        player.teleport(at,{dimension:player.dimension,checkForBlocks:true});
        cooldown.set(player.id,now);tell(player,"Teleporte ativado.");return;
      }catch{}
    }
    tell(player,"Nenhum destino livre com chão seguro nessa direção.");return;
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
      .body("Escolha sua origem. Os poderes Java ainda estão em conversão; este pacote implementa apenas os efeitos listados.\nAtual: "+(prev??"nenhuma"));
    for(const item of ORIGINS_CATALOG){
      const flag=IMPLEMENTED_PASSIVES[item.id]?"[passivo]":"[catálogo]";
      form.button(item.label+" "+flag);
    }
    const choice=await form.show(player);
    if(choice.canceled||choice.selection===undefined)return;
    const selected=ORIGINS_CATALOG[choice.selection];
    if(!selected)return;
    player.setDynamicProperty(KEY,selected.id);
    tell(player,"Origem selecionada: "+selected.label+". Poderes do Java ainda não foram integralmente portados.");
  }catch(e){tell(player,"Não foi possível abrir Origins: "+String(e));}
  finally{busy.delete(player.id);}
}
export function installOrigins(){
  world.afterEvents.playerLeave.subscribe(({playerId})=>cooldown.delete(playerId));
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
    enderian:"teleporte seguro + vulnerabilidade à água",
    feline:"visão noturna + salto de sprint + imunidade a queda",
    merling:"respiração/visão aquática + velocidade na água",
    phantom:"invisibilidade agachado + ativação temporária",
    shulk:"resistência + pressa (inventário extra não portado)"
  };
  tell(player,o?"Sua origem: "+o.label+" ("+(implemented[id]??"sem poderes portados")+")":"Nenhuma origem selecionada. Digite !minizin origins.");
}
