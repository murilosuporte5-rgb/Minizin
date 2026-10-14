import {world, system, EntityDamageCause, ItemStack} from '@minecraft/server';
import {planAttack} from './combat.js';
import {CREATURES} from './creature_catalog.js';

const attacks = new Map();
const retaliation = new Map();
const DRAGONS = {
  'minizin_iceandfire:firedragon': {kind:'fire', dragon:'minizin_iceandfire:firedragon', prefix:'minizin_iceandfire'},
  'minizin_iceandfire:icedragon': {kind:'ice', dragon:'minizin_iceandfire:icedragon', prefix:'minizin_iceandfire'},
  'minizin_iceandfire:lightningdragon': {kind:'lightning', dragon:'minizin_iceandfire:lightningdragon', prefix:'minizin_iceandfire'},
  'minizin_creatures:fire_dragon': {kind:'fire', dragon:'minizin_creatures:fire_dragon', prefix:'minizin_creatures'},
  'minizin_creatures:ice_dragon': {kind:'ice', dragon:'minizin_creatures:ice_dragon', prefix:'minizin_creatures'},
  'minizin_creatures:lightning_dragon': {kind:'lightning', dragon:'minizin_creatures:lightning_dragon', prefix:'minizin_creatures'}
};
const DRAGON_EGGS = {
  'minizin_iceandfire:dragon_egg_fire': {kind:'fire', prefix:'minizin_iceandfire'},
  'minizin_iceandfire:dragon_egg_ice': {kind:'ice', prefix:'minizin_iceandfire'},
  'minizin_iceandfire:dragon_egg_lightning': {kind:'lightning', prefix:'minizin_iceandfire'},
  'minizin_creatures:dragon_egg_fire': {kind:'fire', prefix:'minizin_creatures'},
  'minizin_creatures:dragon_egg_ice': {kind:'ice', prefix:'minizin_creatures'},
  'minizin_creatures:dragon_egg_lightning': {kind:'lightning', prefix:'minizin_creatures'}
};
const DRAGON_ARMOR = new Map([
  ['minizin_iceandfire:dragon_armor_iron',{material:'iron',slot:'head'}],
  ...['iron','gold','diamond','silver','copper','dragonsteel_fire','dragonsteel_ice','dragonsteel_lightning']
    .flatMap(material=>['head','neck','body','tail'].map(slot=>[
      'minizin_iceandfire:dragonarmor_'+material+'_'+slot,{material,slot}
    ]))
]);
const DRAGON_ARMOR_ORDINAL = {
  iron: 1, gold: 2, diamond: 3, silver: 4, fire: 5, ice: 6,
  copper: 7, lightning: 8, dragonsteel_fire: 5,
  dragonsteel_ice: 6, dragonsteel_lightning: 8,
};
const DRAGON_ARMOR_SLOTS = ['head', 'neck', 'body', 'tail'];
const DAY_TICKS = 24000;
const dragonKey = (entity,key,fallback='') => {
  try { return entity.getDynamicProperty('minizin:dragon_'+key) ?? fallback; }
  catch { return fallback; }
};
const setDragonKey = (entity,key,value) => {
  try { entity.setDynamicProperty('minizin:dragon_'+key,value); } catch {}
};
function syncDragonArmorProperty(entity, slot, material) {
  const ordinal = Number(DRAGON_ARMOR_ORDINAL[material] ?? material ?? 0);
  if (!DRAGON_ARMOR_SLOTS.includes(slot) || !Number.isInteger(ordinal) || ordinal < 0 || ordinal > 8) return;
  try { entity.setProperty('minizin:armor_'+slot, ordinal); } catch {}
}
const dragonStage = days => days >= 100 ? 5 : days >= 75 ? 4 : days >= 50 ? 3 : days >= 25 ? 2 : 1;
const dragonInfo = entity => DRAGONS[entity.typeId];
const heldItem = player => {
  try { return player.getComponent('minecraft:inventory')?.container?.getItem(player.selectedSlotIndex)?.typeId; }
  catch { return undefined; }
};
const consumeHeld = (player,typeId) => {
  if (player.getGameMode?.() === 'Creative') return true;
  try {
    const inventory=player.getComponent('minecraft:inventory')?.container;
    const slot=player.selectedSlotIndex,stack=inventory?.getItem(slot);
    if (!stack || stack.typeId!==typeId) return false;
    if (stack.amount<=1) inventory.setItem(slot,undefined);
    else { stack.amount-=1; inventory.setItem(slot,stack); }
    return true;
  } catch { return false; }
};
const dragonOwner = entity => String(dragonKey(entity,'owner',''));
const dragonArmor = itemId => DRAGON_ARMOR.get(itemId) ?? (
  itemId==='minizin_iceandfire:dragon_armor_iron' ? {material:'iron',slot:'head'} : null
);
function setDragonState(entity,state) {
  try { entity.setProperty('minizin:flying',state); } catch {}
  try { entity.triggerEvent(state ? 'minizin:takeoff' : 'minizin:land'); } catch {}
}
// Bedrock does not expose Java's player xxa/zza ride inputs to scripts. Use the
// camera vector for forward/vertical steering and native rideable movement for
// the mobile strafe/backward input. The velocity damping keeps the mount
// controllable instead of accumulating impulses every five ticks.
function dragonRiderImpulse(rider, entity) {
  const view=rider.getViewDirection?.()??{x:0,y:0,z:0};
  const horizontal=Math.hypot(view.x,view.z);
  const speed=rider.isSprinting ? 0.20 : 0.16;
  const velocity=entity.getVelocity?.()??{x:0,y:0,z:0};
  const lift=Math.max(-0.08,Math.min(0.14,view.y*0.22-velocity.y*0.45));
  return {
    x: horizontal>0.001 ? view.x/horizontal*speed : -velocity.x*0.08,
    y: lift,
    z: horizontal>0.001 ? view.z/horizontal*speed : -velocity.z*0.08
  };
}
function dragonTick(entity) {
  const info=dragonInfo(entity); if(!info) return;
  const age=Number(dragonKey(entity,'age_ticks',0))+5;
  let days=Number(dragonKey(entity,'days',0));
  if(age>=DAY_TICKS) { days+=Math.floor(age/DAY_TICKS); setDragonKey(entity,'age_ticks',age%DAY_TICKS); }
  else setDragonKey(entity,'age_ticks',age);
  setDragonKey(entity,'days',days);
  const stage=dragonStage(days),previous=Number(dragonKey(entity,'stage',0));
  if(stage!==previous) {
    setDragonKey(entity,'stage',stage);
    try { entity.triggerEvent('minizin:stage_'+stage); } catch {}
  }
  for (const slot of DRAGON_ARMOR_SLOTS)
    syncDragonArmorProperty(entity, slot, dragonKey(entity, 'armor_'+slot, 0));
  const rider=entity.getComponent('minecraft:rideable')?.getRiders?.().find(x=>x.typeId==='minecraft:player');
  const persistedFlight=Boolean(dragonKey(entity,'flight',false));
  if (stage>=3 && dragonOwner(entity) && Boolean(entity.getProperty?.('minizin:flying'))!==persistedFlight)
    setDragonState(entity,persistedFlight);
  if(rider && dragonOwner(entity)===rider.id && stage>=3) {
    if(persistedFlight) {
      try { entity.applyImpulse(dragonRiderImpulse(rider,entity)); } catch {}
    }
  }
}
function tickDragonEgg(entity) {
  const info=DRAGON_EGGS[entity.typeId]; if(!info) return;
  const dim=entity.dimension,pos=entity.location;
  let eligible=false,frozen=Boolean(dragonKey(entity,'frozen',false));
  const near=(ids) => ids.some(id=>{try{return dim.getBlock({x:Math.floor(pos.x),y:Math.floor(pos.y),z:Math.floor(pos.z)})?.typeId===id;}catch{return false;}});
  if(info.kind==='fire') eligible=near(['minecraft:fire','minecraft:soul_fire','minecraft:campfire']);
  if(info.kind==='ice') {
    if(!frozen && near(['minecraft:water'])) { setDragonKey(entity,'frozen',true); frozen=true; }
    eligible=frozen;
  }
  if(info.kind==='lightning') {
    try { eligible=Boolean(dim.getTopmostBlock({x:Math.floor(pos.x),z:Math.floor(pos.z)})) && /rain|thunder/i.test(String(dim.getWeather?.()??'')); }
    catch { eligible=false; }
  }
  if(!eligible) return;
  const incubation=Number(dragonKey(entity,'incubation',0))+5;
  setDragonKey(entity,'incubation',incubation);
  if(incubation<7200) return;
  const dragonId=info.prefix+':'+({fire:'firedragon',ice:'icedragon',lightning:'lightningdragon'}[info.kind]);
  try {
    const baby=dim.spawnEntity(dragonId,{x:pos.x,y:pos.y+1,z:pos.z});
    const owner=dragonOwner(entity); if(owner) setDragonKey(baby,'owner',owner);
    setDragonKey(baby,'days',0);setDragonKey(baby,'age_ticks',0);entity.remove();
  } catch {}
}
function installDragonInteractions() {
  world.afterEvents.playerInteractWithEntity.subscribe(event=>{
    const entity=event.target,info=dragonInfo(entity); if(!info) return;
    system.run(()=>{
      if(!entity.isValid||!event.player?.isValid)return;
      const player=event.player,item=event.beforeItemStack?.typeId??heldItem(player),owner=dragonOwner(entity);
      if(item===info.prefix+':creative_dragon_meal'&&!owner) {
        setDragonKey(entity,'owner',player.id);consumeHeld(player,item);player.sendMessage('Dragão domesticado.');return;
      }
      if(owner!==player.id)return;
      if(item===info.prefix+':dragon_meal') {
        setDragonKey(entity,'days',Number(dragonKey(entity,'days',0))+1);consumeHeld(player,item);
        player.sendMessage('Idade: '+dragonKey(entity,'days',0)+' dias / estágio '+dragonStage(Number(dragonKey(entity,'days',0))));return;
      }
      const armor=dragonArmor(item);
      if(armor) {
        const inventory=player.getComponent('minecraft:inventory')?.container;
        const selected=inventory?.getItem(player.selectedSlotIndex);
        if(!selected||selected.typeId!==item||selected.amount!==1){
          player.sendMessage('Use uma única peça de armadura selecionada para equipar.');return;
        }
        const old=String(dragonKey(entity,'armor_'+armor.slot+'_item',''));
        const oldMaterial=String(dragonKey(entity,'armor_'+armor.slot,''));
        if(old===item){player.sendMessage('Esta peça já está equipada.');return;}
        const creative=String(player.getGameMode?.()).toLowerCase()==='creative';
        try {
          setDragonKey(entity,'armor_'+armor.slot,armor.material);
          setDragonKey(entity,'armor_'+armor.slot+'_item',item);
          syncDragonArmorProperty(entity,armor.slot,armor.material);
          // The selected inventory slot is the transaction boundary: in
          // Survival it receives the previous piece, so replacing armor can
          // never silently delete a Java source-backed item.
          if(!creative)inventory.setItem(player.selectedSlotIndex,old?new ItemStack(old,1):undefined);
        } catch(error) {
          setDragonKey(entity,'armor_'+armor.slot,oldMaterial);
          setDragonKey(entity,'armor_'+armor.slot+'_item',old);
          player.sendMessage('Não foi possível trocar a armadura: '+String(error));return;
        }
        player.sendMessage('Armadura de '+armor.material+' equipada: '+armor.slot+'.');return;
      }
      if(!item&&dragonStage(Number(dragonKey(entity,'days',0)))>=3) {
        try { entity.getComponent('minecraft:rideable')?.addRider(player); } catch {}
      }
    });
  });
  world.afterEvents.itemUse.subscribe(event=>{
    const player=event.source,item=event.itemStack?.typeId,egg=DRAGON_EGGS[item];
    if(egg) {
      system.run(()=>{
        if(!player?.isValid)return;
        const view=player.getViewDirection?.()??{x:0,y:0,z:0},pos=player.location;
        try {
          const entity=player.dimension.spawnEntity(item.replace('dragon_egg_','')+'_dragon_egg',{x:Math.floor(pos.x+view.x*2)+0.5,y:Math.floor(pos.y),z:Math.floor(pos.z+view.z*2)+0.5});
          setDragonKey(entity,'owner',player.id);setDragonKey(entity,'incubation',0);consumeHeld(player,item);
          player.sendMessage('Ovo '+egg.kind+' colocado; incubação condicionada ao ambiente.');
        } catch {}
      });
      return;
    }
    const info=DRAGONS[player.getComponent('minecraft:riding')?.entityRidingOn?.typeId];
    if(item?.endsWith(':dragon_flute')&&info) {
      const entity=player.getComponent('minecraft:riding')?.entityRidingOn;
      if(dragonOwner(entity)!==player.id)return;
      if(player.isSneaking) { const flight=!Boolean(dragonKey(entity,'flight',false));setDragonKey(entity,'flight',flight);setDragonState(entity,flight);player.sendMessage(flight?'Voo habilitado.':'Pouso ativado.'); }
    }
  });
}
installDragonInteractions();
const SPECIAL_BOSSES = new Set([
  'minizin_cataclysm:ignis','minizin_cataclysm:harbinger',
  'minizin_cataclysm:ender_guardian','minizin_mowzies:bluff'
]);
const MOWZIE_ENTITIES = new Set([
  'minizin_mowzies:foliaath','minizin_mowzies:frostmaw',
  'minizin_mowzies:grottol','minizin_mowzies:naga',
  'minizin_mowzies:wroughtnaut'
]);
const bossKey = (entity,key,fallback=0) => {
  try { return entity.getDynamicProperty('minizin:boss_'+key) ?? fallback; }
  catch { return fallback; }
};
const setBossKey = (entity,key,value) => {
  try { entity.setDynamicProperty('minizin:boss_'+key,value); } catch {}
};
const segmentDistance = (point,from,to) => {
  const dx=to.x-from.x,dz=to.z-from.z;
  const t=Math.max(0,Math.min(1,((point.x-from.x)*dx+(point.z-from.z)*dz)/Math.max(0.001,dx*dx+dz*dz)));
  return Math.hypot(point.x-(from.x+t*dx),point.z-(from.z+t*dz));
};
function bossStrike(entity,target,damage,particle='minecraft:basic_smoke_particle',knock=0) {
  try {
    target.applyDamage(damage,{cause:EntityDamageCause.entityAttack,damagingEntity:entity});
    if(knock) target.applyImpulse({x:0,y:knock,z:0});
    entity.dimension.spawnParticle(particle,target.location);
    entity.setProperty('minizin:attacking',true);
  } catch {}
}
function mowzieState(entity,state) {
  try { entity.setProperty('minizin_mowzies:attack',state); } catch {}
  try { entity.setProperty('minizin:attacking',state!=='idle'); } catch {}
}
function mowzieAreaStrike(entity,range,damage,particle,knock=0) {
  try {
    for (const player of entity.dimension.getPlayers({location:entity.location,maxDistance:range}))
      bossStrike(entity,player,damage,particle,knock);
  } catch {}
}
function sourceMowzieAttack(entity,target,tick,health) {
  if (!MOWZIE_ENTITIES.has(entity.typeId)||!target)return false;
  const distanceTo=length(difference(target.location,entity.location));
  const cooldown=Number(bossKey(entity,'cooldown',0));
  if(tick<cooldown)return false;
  const ratio=health.currentValue/Math.max(1,health.effectiveMax);
  if(entity.typeId==='minizin_mowzies:foliaath'&&distanceTo<=4) {
    setBossKey(entity,'cooldown',tick+14);mowzieState(entity,'bite');bossStrike(entity,target,4,'minecraft:basic_smoke_particle',0.25);return true;
  }
  if(entity.typeId==='minizin_mowzies:frostmaw') {
    if(distanceTo<=6.5) {
      setBossKey(entity,'cooldown',tick+28);mowzieState(entity,Math.random()<0.35?'swipe_twice':'swipe');mowzieAreaStrike(entity,6.5,12,'minecraft:basic_smoke_particle',0.45);return true;
    }
    if(ratio<0.6&&distanceTo<=8.5) {
      setBossKey(entity,'cooldown',tick+113);mowzieState(entity,'slam');mowzieAreaStrike(entity,8.5,14,'minecraft:basic_smoke_particle',0.8);return true;
    }
    if(distanceTo<=13.5) {
      setBossKey(entity,'cooldown',tick+92);mowzieState(entity,'ice_breath');try{target.addEffect('slowness',80,{amplifier:1});}catch{};bossStrike(entity,target,8,'minecraft:basic_smoke_particle',0.15);return true;
    }
    if(distanceTo<=24) {
      setBossKey(entity,'cooldown',tick+50);mowzieState(entity,'ice_ball');try{target.addEffect('slowness',60,{amplifier:2});}catch{};bossStrike(entity,target,9,'minecraft:basic_smoke_particle',0.25);return true;
    }
  }
  if(entity.typeId==='minizin_mowzies:naga') {
    if(distanceTo<=8) {
      setBossKey(entity,'cooldown',tick+54);mowzieState(entity,'swoop');bossStrike(entity,target,10,'minecraft:basic_smoke_particle',0.65);return true;
    }
    if(distanceTo<=24) {
      setBossKey(entity,'cooldown',tick+50);mowzieState(entity,'spit');try{target.addEffect('poison',60,{amplifier:0});}catch{};bossStrike(entity,target,7,'minecraft:basic_smoke_particle',0.2);return true;
    }
  }
  if(entity.typeId==='minizin_mowzies:wroughtnaut') {
    if(distanceTo<=5) {
      setBossKey(entity,'cooldown',tick+50);mowzieState(entity,'attack');mowzieAreaStrike(entity,5,16,'minecraft:basic_smoke_particle',0.65);return true;
    }
    if(distanceTo<=9) {
      setBossKey(entity,'cooldown',tick+40);mowzieState(entity,'vertical_attack');mowzieAreaStrike(entity,9,14,'minecraft:basic_smoke_particle',0.8);return true;
    }
    if(distanceTo<=12) {
      setBossKey(entity,'cooldown',tick+40);mowzieState(entity,'stomp');mowzieAreaStrike(entity,12,10,'minecraft:basic_smoke_particle',0.55);return true;
    }
  }
  return false;
}
function specialBossAttack(entity,target,tick,health) {
  if(!SPECIAL_BOSSES.has(entity.typeId)||!target)return false;
  const distanceTo=length(difference(target.location,entity.location));
  const cooldown=Number(bossKey(entity,'cooldown',0));
  if(tick<cooldown)return false;
  const ratio=health.currentValue/Math.max(1,health.effectiveMax);
  if(entity.typeId==='minizin_cataclysm:ignis') {
    const phase=ratio<=1/3?2:ratio<=2/3?1:0;setBossKey(entity,'phase',phase);
    if(phase===2&&distanceTo<=24) {
      setBossKey(entity,'cooldown',tick+140);setBossKey(entity,'move','hellfire_burst');
      bossStrike(entity,target,18,'minecraft:basic_flame_particle',0.45);try{target.setOnFire(5,true);}catch{};return true;
    }
    if(phase>=1&&distanceTo>7&&distanceTo<=20) {
      setBossKey(entity,'cooldown',tick+80);setBossKey(entity,'move','flame_wave');
      bossStrike(entity,target,12,'minecraft:basic_flame_particle',0.25);try{target.setOnFire(3,true);}catch{};return true;
    }
    if(distanceTo<=7) {
      setBossKey(entity,'cooldown',tick+45);setBossKey(entity,'move','sword_slash');
      bossStrike(entity,target,10,'minecraft:basic_smoke_particle',0.55);return true;
    }
  }
  if(entity.typeId==='minizin_cataclysm:harbinger'&&distanceTo<=32) {
    setBossKey(entity,'cooldown',tick+100);setBossKey(entity,'move','laser');
    const players=entity.dimension.getPlayers({location:entity.location,maxDistance:32});
    for(const player of players) if(segmentDistance(player.location,entity.location,target.location)<=2.5)
      bossStrike(entity,player,14,'minecraft:basic_flame_particle',0.15);
    return true;
  }
  if(entity.typeId==='minizin_cataclysm:ender_guardian') {
    if(distanceTo<=6) {
      setBossKey(entity,'cooldown',tick+65);setBossKey(entity,'move','stomp');
      bossStrike(entity,target,13,'minecraft:basic_smoke_particle',0.8);return true;
    }
    if(distanceTo<=18) {
      setBossKey(entity,'cooldown',tick+120);setBossKey(entity,'move','blackhole');
      bossStrike(entity,target,11,'minecraft:basic_portal_particle',0.25);try{target.addEffect('slowness',80,{amplifier:2});}catch{};return true;
    }
    if(distanceTo<=32) {
      setBossKey(entity,'cooldown',tick+180);setBossKey(entity,'move','air_strike');
      bossStrike(entity,target,15,'minecraft:basic_smoke_particle',0.35);return true;
    }
  }
  if(entity.typeId==='minizin_mowzies:bluff'&&distanceTo<=18) {
    setBossKey(entity,'cooldown',tick+90);setBossKey(entity,'move','fissure');
    const players=entity.dimension.getPlayers({location:entity.location,maxDistance:20});
    for(const player of players) if(segmentDistance(player.location,entity.location,target.location)<=3)
      bossStrike(entity,player,9,'minecraft:basic_smoke_particle',0.2);
    return true;
  }
  return false;
}
world.afterEvents.entityHurt.subscribe(({hurtEntity,damageSource}) => {
  if (CREATURES[hurtEntity.typeId]?.kind === 'atlatitan' && damageSource.damagingEntity?.typeId === 'minecraft:player')
    retaliation.set(hurtEntity.id,{player:damageSource.damagingEntity.id,until:system.currentTick+200});
});
const length = v => Math.hypot(v.x, v.y, v.z);
const difference = (a,b) => ({x:a.x-b.x,y:a.y-b.y,z:a.z-b.z});
/** @param {import('@minecraft/server').Entity} entity @param {import('@minecraft/server').Entity} target */
function visible(entity, target) {
  const origin = entity.getHeadLocation(), ray = difference(target.getHeadLocation(), origin);
  const distance = length(ray);
  if (distance < 0.01) return true;
  const hit = entity.dimension.getBlockFromRay(origin,
    {x:ray.x/distance,y:ray.y/distance,z:ray.z/distance}, {maxDistance:distance});
  return !hit;
}

// No world destruction, entity respawning or perpetual entity references.
system.runInterval(() => {
  const seen = new Set();
  /** @type {Map<string, import('@minecraft/server').Player[]>} */
  const playersByDimension = new Map();
  for (const p of world.getAllPlayers()) {
    const mode = String(p.getGameMode()).toLowerCase();
    if (!['survival','adventure'].includes(mode)) continue;
    const key = p.dimension.id;
    if (!playersByDimension.has(key)) playersByDimension.set(key, []);
    playersByDimension.get(key).push(p);
  }
  for (const players of playersByDimension.values()) {
    const dimension = players[0].dimension;
    let processed = 0;
    for (const player of players) {
      for (const entity of dimension.getEntities({location:player.location,maxDistance:32,families:['minizin_creature','minizin_mowzies']})) {
        if (seen.has(entity.id) || processed >= 48) continue;
        seen.add(entity.id); processed++;
        try {
          const spec = CREATURES[entity.typeId];
          const isMowzie=MOWZIE_ENTITIES.has(entity.typeId);
          if ((!spec&&!isMowzie) || !entity.isValid) continue;
          dragonTick(entity);
          const owner=spec.kind==='dragon' ? dragonOwner(entity) : '';
          const rider=spec.kind==='dragon' ? entity.getComponent('minecraft:rideable')?.getRiders?.().find(x=>x.typeId==='minecraft:player') : null;
          const riderIsOwner=Boolean(rider && rider.id===owner && Number(dragonKey(entity,'days',0))>=50);
          if (riderIsOwner) {
            // Java DragonAIRide takes over navigation/targeting while mounted.
            // Do not let the combat adaptation below fight the player's input.
            entity.setProperty('minizin:attacking',false);
            continue;
          }
          const candidates = players.filter(p => p.isValid)
            .map(p=>({player:p,distance:length(difference(p.location,entity.location))}))
            .filter(p=>p.distance<=24 && p.player.id!==owner).sort((a,b)=>a.distance-b.distance);
          const closest = candidates[0];
          if (!closest) {
            entity.setProperty('minizin:attacking',false);
            if(isMowzie)mowzieState(entity,'idle');
            if(spec?.kind==='dragon'&&entity.getProperty('minizin:flying')){
              entity.triggerEvent('minizin:land');entity.setProperty('minizin:flying',false);
            }
            continue;
          }
          if (isMowzie) {
            const health=entity.getComponent('minecraft:health');
            if (!health || !sourceMowzieAttack(entity,closest.player,system.currentTick,health)) mowzieState(entity,'idle');
            continue;
          }
          if (spec.kind === 'atlatitan') {
            const revenge=retaliation.get(entity.id);
            if (!revenge || revenge.until<system.currentTick || revenge.player!==closest.player.id) continue;
          }
          const health = entity.getComponent('minecraft:health');
          entity.setProperty('minizin:enraged', health.currentValue < health.effectiveMax/2);
          if (specialBossAttack(entity,closest.player,system.currentTick,health)) continue;
          // Flight is a combat adaptation: native flying navigation plus bounded lift.
          const flying = spec.kind==='dragon' && closest.distance>5 && closest.distance<24;
          if (flying !== entity.getProperty('minizin:flying')) {
            entity.triggerEvent(flying ? 'minizin:takeoff' : 'minizin:land');
            entity.setProperty('minizin:flying', flying);
          }
          entity.setProperty('minizin:attacking', false);
          if (flying && visible(entity, closest.player)) {
            const d = difference(closest.player.location,entity.location), n = Math.max(1,length(d));
            const vy = entity.getVelocity().y;
            entity.applyImpulse({x:d.x/n*0.08,z:d.z/n*0.08,
              y:Math.max(-0.15,Math.min(0.2,(closest.player.location.y+4-entity.location.y)*0.025-vy*0.5))});
          }
          const attack = planAttack(spec.kind, closest.distance,
            health.currentValue/health.effectiveMax, system.currentTick, attacks.get(entity.id));
          if (!attack || !visible(entity,closest.player)) continue;
          attacks.set(entity.id,system.currentTick);
          entity.setProperty('minizin:attacking', true);
          const center = attack.attack==='breath' ? closest.player.location : entity.location;
          if (spec.sound) dimension.playSound(spec.sound,entity.location,{volume:1,pitch:1});
          dimension.spawnParticle(attack.attack==='breath'?'minecraft:basic_flame_particle':'minecraft:basic_smoke_particle',center);
          for (const candidate of candidates) {
            if (length(difference(candidate.player.location,center))>attack.radius || !visible(entity,candidate.player)) continue;
            candidate.player.applyDamage(attack.damage,{cause:EntityDamageCause.entityAttack,damagingEntity:entity});
            if (spec.element==='fire' && attack.attack==='breath') candidate.player.setOnFire(3,true);
            if (spec.element==='ice' && attack.attack==='breath') candidate.player.addEffect('slowness',60,{amplifier:1});
            if (attack.attack==='slam' || attack.attack==='stomp') candidate.player.applyImpulse({x:0,y:0.4,z:0});
          }
        } catch (error) { console.warn('[Minizin creatures]',entity.typeId,String(error)); }
      }
      for (const egg of dimension.getEntities({location:player.location,maxDistance:32,families:['minizin_dragon_egg']})) {
        if (seen.has(egg.id)) continue;
        seen.add(egg.id);tickDragonEgg(egg);
      }
    }
  }
  for (const id of attacks.keys()) if (!seen.has(id)) attacks.delete(id);
  for (const [id,r] of retaliation) if (!seen.has(id) || r.until<system.currentTick) retaliation.delete(id);
}, 5);
