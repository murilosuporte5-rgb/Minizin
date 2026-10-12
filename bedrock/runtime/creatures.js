import {world, system, EntityDamageCause} from '@minecraft/server';
import {planAttack} from './combat.js';
import {CREATURES} from './creature_catalog.js';

const attacks = new Map();
const retaliation = new Map();
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
          const candidates = players.filter(p => p.isValid)
            .map(p=>({player:p,distance:length(difference(p.location,entity.location))}))
            .filter(p=>p.distance<=24).sort((a,b)=>a.distance-b.distance);
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
    }
  }
  for (const id of attacks.keys()) if (!seen.has(id)) attacks.delete(id);
  for (const [id,r] of retaliation) if (!seen.has(id) || r.until<system.currentTick) retaliation.delete(id);
}, 5);
