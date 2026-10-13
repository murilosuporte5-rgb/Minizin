import {world, system, EntityDamageCause} from '@minecraft/server';
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
const DAY_TICKS = 24000;
const dragonKey = (entity,key,fallback='') => {
  try { return entity.getDynamicProperty('minizin:dragon_'+key) ?? fallback; }
  catch { return fallback; }
};
const setDragonKey = (entity,key,value) => {
  try { entity.setDynamicProperty('minizin:dragon_'+key,value); } catch {}
};
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
function setDragonState(entity,state) {
  try { entity.setProperty('minizin:flying',state); } catch {}
  try { entity.triggerEvent(state ? 'minizin:takeoff' : 'minizin:land'); } catch {}
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
  const rider=entity.getComponent('minecraft:rideable')?.getRiders?.().find(x=>x.typeId==='minecraft:player');
  if(rider && dragonOwner(entity)===rider.id && stage>=3) {
    if(Boolean(dragonKey(entity,'flight',false))) {
      const view=rider.getViewDirection?.()??{x:0,y:0,z:0};
      try { entity.applyImpulse({x:view.x*0.13,y:Math.max(-0.07,Math.min(0.15,view.y*0.18)),z:view.z*0.13}); } catch {}
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
      if(item===info.prefix+':dragon_armor_iron') {
        const armor=Math.min(4,Number(dragonKey(entity,'armor',0))+1);setDragonKey(entity,'armor',armor);consumeHeld(player,item);
        player.sendMessage('Armadura equipada: '+armor+'/4');return;
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
      for (const entity of dimension.getEntities({location:player.location,maxDistance:32,families:['minizin_creature']})) {
        if (seen.has(entity.id) || processed >= 48) continue;
        seen.add(entity.id); processed++;
        try {
          const spec = CREATURES[entity.typeId];
          if (!spec || !entity.isValid) continue;
          dragonTick(entity);
          const owner=spec.kind==='dragon' ? dragonOwner(entity) : '';
          const candidates = players.filter(p => p.isValid)
            .map(p=>({player:p,distance:length(difference(p.location,entity.location))}))
            .filter(p=>p.distance<=24 && p.player.id!==owner).sort((a,b)=>a.distance-b.distance);
          const closest = candidates[0];
          if (!closest) {
            entity.setProperty('minizin:attacking',false);
            if(spec.kind==='dragon'&&entity.getProperty('minizin:flying')){
              entity.triggerEvent('minizin:land');entity.setProperty('minizin:flying',false);
            }
            continue;
          }
          if (spec.kind === 'atlatitan') {
            const revenge=retaliation.get(entity.id);
            if (!revenge || revenge.until<system.currentTick || revenge.player!==closest.player.id) continue;
          }
          const health = entity.getComponent('minecraft:health');
          entity.setProperty('minizin:enraged', health.currentValue < health.effectiveMax/2);
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
