import {world, system, EntityDamageCause, ItemStack} from '@minecraft/server';
import {planAttack,planUmvuthiAttack} from './combat.js';
import {CREATURES} from './creature_catalog.js';
import {ARMOR_MATERIALS,ARMOR_SLOTS,armorOrdinal,armorRating} from './dragon_armor.js';

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
  ...ARMOR_MATERIALS
    .flatMap(material=>ARMOR_SLOTS.map(slot=>[
      'minizin_iceandfire:dragonarmor_'+material+'_'+slot,{material,slot}
    ]))
]);
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
const dragonArmor = itemId => DRAGON_ARMOR.get(itemId) ?? (
  itemId==='minizin_iceandfire:dragon_armor_iron' ? {material:'iron',slot:'head'} : null
);
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
  if(info.prefix==='minizin_iceandfire') {
    const materials=Object.fromEntries(ARMOR_SLOTS.map(slot=>[slot,dragonKey(entity,'armor_'+slot,'')]));
    for(const slot of ARMOR_SLOTS) {
      const ordinal=armorOrdinal(materials[slot]);
      if(entity.getProperty('minizin:armor_'+slot)!==ordinal)
        entity.setProperty('minizin:armor_'+slot,ordinal);
    }
    const rating=armorRating(materials);
    if(Number(dragonKey(entity,'armor_applied',-1))!==rating) {
      entity.triggerEvent('minizin:dragon_armor_'+rating);
      setDragonKey(entity,'armor_applied',rating);
    }
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
      const armor=dragonArmor(item);
      if(armor) {
        const inventory=player.getComponent('minecraft:inventory')?.container;
        const slot=player.selectedSlotIndex,stack=inventory?.getItem(slot);
        if(player.getGameMode?.()!=='Creative'&&(!stack||stack.typeId!==item||stack.amount!==1))return;
        const old=String(dragonKey(entity,'armor_'+armor.slot+'_item',''));
        if(old===item){player.sendMessage('Esta peça já está equipada.');return;}
        try {
          entity.setDynamicProperty('minizin:dragon_armor_'+armor.slot,armor.material);
          entity.setDynamicProperty('minizin:dragon_armor_'+armor.slot+'_item',item);
          if(player.getGameMode?.()!=='Creative')inventory.setItem(slot,old?new ItemStack(old,1):undefined);
        } catch(error) {
          try {
            entity.setDynamicProperty('minizin:dragon_armor_'+armor.slot,old ?
              ARMOR_MATERIALS.find(material=>old.includes('dragonarmor_'+material+'_'))??'iron' : '');
            entity.setDynamicProperty('minizin:dragon_armor_'+armor.slot+'_item',old);
          } catch {}
          player.sendMessage('Não foi possível trocar a armadura: '+String(error));return;
        }
        // The synced texture and protection follow on the next creature tick.
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
  'minizin_cataclysm:ender_guardian','minizin_mowzies:bluff',
  'minizin_mowzies:umvuthi'
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
function tickUmvuthi(entity,target,tick,health){
  let mode=Number(bossKey(entity,'mode',0));
  const start=Number(bossKey(entity,'start',tick));
  const elapsed=tick-start;
  const duration=mode===1?25:mode===2?30:100;
  if(mode&&(elapsed<0||elapsed>=duration)){
    mode=0;setBossKey(entity,'mode',0);
    entity.setProperty('minizin:attack_mode',0);
    entity.setProperty('minizin:attacking',false);
  }
  const players=entity.dimension.getPlayers({location:entity.location,maxDistance:24});
  if(mode){
    if(mode===1&&elapsed>=9&&!bossKey(entity,'impact',false)){
      setBossKey(entity,'impact',true);
      for(const player of players)if(length(difference(player.location,target.location))<=2.5&&visible(entity,player)){
        bossStrike(entity,player,9,'minecraft:basic_flame_particle',0.25);
        try{player.setOnFire(3,true);}catch{}
      }
    }
    if(mode===2&&elapsed>=12&&!bossKey(entity,'impact',false)){
      setBossKey(entity,'impact',true);
      for(const player of players){
        const d=difference(player.location,entity.location),range=length(d);
        if(range>4||!visible(entity,player))continue;
        bossStrike(entity,player,8,'minecraft:basic_flame_particle');
        try{player.applyImpulse({x:d.x/Math.max(1,range)*0.9,y:0.3,z:d.z/Math.max(1,range)*0.9});}catch{}
      }
    }
    if(mode===3&&elapsed>=22&&elapsed<90&&tick-Number(bossKey(entity,'last_beam',-1000))>=10){
      setBossKey(entity,'last_beam',tick);
      for(const player of players)
        if(segmentDistance(player.location,entity.location,target.location)<=1.5&&
           length(difference(player.location,entity.location))<=24&&visible(entity,player)){
          bossStrike(entity,player,4,'minecraft:basic_flame_particle');
          try{player.setOnFire(2,true);}catch{}
        }
    }
    if(mode===4){
      if(elapsed<30)for(const player of players){
        const d=difference(entity.location,player.location),range=length(d);
        if(range>16||range<0.5)continue;
        try{player.applyImpulse({x:d.x/range*0.03,y:0.075,z:d.z/range*0.03});}catch{}
      }
      if(elapsed>=44&&!bossKey(entity,'impact',false)){
        setBossKey(entity,'impact',true);
        for(const player of players)if(length(difference(player.location,entity.location))<=10&&visible(entity,player))
          bossStrike(entity,player,16,'minecraft:basic_flame_particle',0.6);
      }
    }
    return true;
  }
  const ready=key=>{
    const value=Number(bossKey(entity,key,0));
    return value-tick>10000?0:value; // world tick may restart after a reload
  };
  const attack=planUmvuthiAttack(length(difference(target.location,entity.location)),
    health.currentValue/Math.max(1,health.effectiveMax),tick,
    {supernova:ready('supernova_ready'),beam:ready('beam_ready'),sunstrike:ready('sunstrike_ready')});
  if(!attack||tick<ready('cooldown'))return false;
  setBossKey(entity,'mode',attack.mode);setBossKey(entity,'start',tick);
  setBossKey(entity,'impact',false);setBossKey(entity,'cooldown',tick+attack.duration+10);
  if(attack.mode===4)setBossKey(entity,'supernova_ready',tick+attack.repeat);
  if(attack.mode===3)setBossKey(entity,'beam_ready',tick+attack.repeat);
  if(attack.mode===1)setBossKey(entity,'sunstrike_ready',tick+attack.repeat);
  entity.setProperty('minizin:attack_mode',attack.mode);
  entity.setProperty('minizin:attacking',true);
  try { if(attack.mode===4)entity.dimension.playSound('minizin.mowzies.umvuthi.attack',entity.location); }
  catch{}
  return true;
}
function specialBossAttack(entity,target,tick,health) {
  if(!SPECIAL_BOSSES.has(entity.typeId)||!target)return false;
  if(entity.typeId==='minizin_mowzies:umvuthi')return tickUmvuthi(entity,target,tick,health);
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
            if(spec.kind==='umvuthi'){
              setBossKey(entity,'mode',0);
              entity.setProperty('minizin:attack_mode',0);
            }
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
