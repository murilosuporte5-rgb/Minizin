/* Minizin The Aether: distinct Java-source-inspired dungeon boss state machines.
 * Java sources: Slider, ValkyrieQueen, SunSpirit at pinned Git submodule.
 * Health (400/500/500), weapon gate, Valkyrie dialogue/lunge/thunder crystals,
 * Sun fire and ice weakness are adapted using real @minecraft/server APIs.
 * No claim that combat timing, boss/model animations or hitbox equals NeoForge.
 */
import { world, system, ItemStack, BlockPermutation } from "@minecraft/server";
import { DUNGEON_REWARDS } from "./dungeon_loot.js";

const D = "minizin_aether:";
const STAGES = Object.freeze({
  slider: { tier: "bronze", health: 400, range: 28 },
  valkyrie_queen: { tier: "silver", health: 500, range: 32 },
  sun_spirit: { tier: "gold", health: 500, range: 38 },
});
const UNLOCK = {
  "locked_carved_stone": "carved_stone",
  "locked_sentry_stone": "sentry_stone",
  "boss_doorway_carved_stone": "minecraft:air",
  "locked_angelic_stone": "angelic_stone",
  "locked_light_angelic_stone": "light_angelic_stone",
  "trapped_angelic_stone": "angelic_stone",
  "trapped_light_angelic_stone": "light_angelic_stone",
  "boss_doorway_angelic_stone": "minecraft:air",
  "treasure_doorway_angelic_stone": "minecraft:air",
  "locked_hellfire_stone": "hellfire_stone",
  "locked_light_hellfire_stone": "light_hellfire_stone",
  "boss_doorway_hellfire_stone": "minecraft:air",
  "treasure_doorway_hellfire_stone": "minecraft:air",
};
const armatures = {
  slider: "animation.minizin_aether.slider.attack",
  valkyrie_queen: "animation.minizin_aether.valkyrie_queen.attack",
  sun_spirit: "animation.minizin_aether.sun_spirit.attack",
};
const ticks = new Map();
const tickNow = () => system.currentTick;
const health = e => e.getComponent("minecraft:health");

function stateFor(e) {
  let s = ticks.get(e.id);
  if (!s) {
    s = { nextAttack: tickNow() + 30, lastCast: 0, lastMinion: 0,
          phase: "idle", strikeCount: 0 };
    ticks.set(e.id, s);
  }
  return s;
}
function data(e, name, fallback = null) {
  try { return e.getDynamicProperty(D + name) ?? fallback; }
  catch { return fallback; }
}
function store(e, name, value) {
  try { e.setDynamicProperty(D + name, value); }
  catch (err) { console.warn("[Aether boss] persistent state failed: " + String(err)); }
}
function nearPlayer(e, radius) {
  let best = null, distance2 = radius * radius;
  for (const player of world.getAllPlayers()) {
    if (player.dimension.id !== e.dimension.id) continue;
    const dx = e.location.x - player.location.x;
    const dy = e.location.y - player.location.y;
    const dz = e.location.z - player.location.z;
    const d2 = dx * dx + dy * dy + dz * dz;
    if (d2 < distance2) { distance2 = d2; best = player; }
  }
  return best && { target: best, distance: Math.sqrt(distance2) };
}
function vec(from, to) {
  const dx = to.x - from.x, dz = to.z - from.z;
  const d = Math.max(.001, Math.hypot(dx, dz));
  return { x: dx / d, z: dz / d };
}
function feedback(e, animation) {
  try { e.playAnimation(animation); } catch { /* content log documents unsupported client */ }
}
function hit(e, p, amount, impulse = 0) {
  try {
    p.applyDamage(amount, { cause: "entityAttack", damagingEntity: e });
    if (impulse) {
      const v = vec(e.location, p.location);
      p.applyImpulse({ x: v.x * impulse, y: .35, z: v.z * impulse });
    }
  } catch (err) { console.warn("[Aether boss] combat hit: " + String(err)); }
}
function chargeSlider(e, p, s, distance) {
  // Slider source: CollideGoal, CrushGoal, BackOffAfterAttackGoal,
  // AvoidObstaclesGoal and directional movement state. Bedrock approximation:
  // short deterministic charge, collision crush, then recovery.
  const n = tickNow();
  if (n < s.nextAttack) return;
  if (distance > 3.4) {
    const direction = vec(e.location, p.location);
    try { e.applyImpulse({ x: direction.x * .48, y: 0, z: direction.z * .48 }); }
    catch { /* heavy block may be stopped by colliders */ }
    feedback(e, armatures.slider);
    s.nextAttack = n + 14;
    s.phase = "charge";
  } else {
    hit(e, p, 15, 1.25);
    feedback(e, armatures.slider);
    s.nextAttack = n + 38;
    s.phase = "recover";
  }
}
function queenCombat(e, p, s, distance) {
  // NeoForge: engage after dialogue; 13.5 melee, LungeGoal and a
  // ThunderCrystalAttackGoal with 450-tick interval in Java.
  if (!data(e, "engaged", false)) return;
  const n = tickNow();
  if (n - s.lastCast >= 450 && distance <= 28) {
    s.lastCast = n;
    s.nextAttack = n + 45;
    s.phase = "thunder";
    feedback(e, armatures.valkyrie_queen);
    p.sendMessage("§dA Rainha Valquíria invoca cristais do trovão!");
    system.runTimeout(() => {
      if (!p.isValid || !e.isValid || p.dimension.id !== e.dimension.id) return;
      const near = nearPlayer(e, 28);
      if (near && near.target.id === p.id) {
        hit(e, p, 9, .65);
        try { e.dimension.spawnParticle("minecraft:basic_crit_particle", p.location); }
        catch { /* particles depend on client version */ }
      }
    }, 17);
    return;
  }
  if (n < s.nextAttack) return;
  if (distance <= 2.7) {
    hit(e, p, 14, .8);
    s.nextAttack = n + 35;
    s.phase = "sword";
    feedback(e, armatures.valkyrie_queen);
  } else if (distance <= 17) {
    const v = vec(e.location, p.location);
    try { e.applyImpulse({ x: v.x * .76, y: .14, z: v.z * .76 }); }
    catch { /* collision */ }
    s.nextAttack = n + 28;
    s.phase = "lunge";
    feedback(e, armatures.valkyrie_queen);
  }
}
function sunCombat(e, p, s, distance) {
  // Original: fireball every 50 ticks, fires/minions ~35 ticks;
  // IceCrystal impact freezes the Sun Spirit and makes it vulnerable.
  const n = tickNow();
  const frozenUntil = Number(data(e, "frozen_until", 0));
  if (frozenUntil > n) {
    s.phase = "frozen";
    try { e.addEffect("minecraft:slowness", 24, { amplifier: 10, showParticles: true }); }
    catch { /* stationary mob */ }
    return;
  }
  if (n - s.lastCast >= 50 && distance < 35) {
    s.lastCast = n;
    s.phase = "fire_volley";
    feedback(e, armatures.sun_spirit);
    p.sendMessage("§6O Espírito do Sol prepara uma rajada incendiária!");
    system.runTimeout(() => {
      if (p.isValid && e.isValid && p.dimension.id === e.dimension.id) {
        const near = nearPlayer(e, 35);
        if (near && near.target.id === p.id) {
          hit(e, p, 10, .25);
          try { p.setOnFire(4, true); } catch { /* unsupported API */ }
        }
      }
    }, 14);
  }
  if (n - s.lastMinion >= 150 && distance < 24) {
    s.lastMinion = n;
    // Fire minions use the source model/texture and their own native BP AI.
    try {
      const near = e.dimension.getEntities({ type: D + "fire_minion",
                                            location: e.location, maxDistance: 28 });
      if (near.length < 3) {
        const minion = e.dimension.spawnEntity(D + "fire_minion", {
          x: e.location.x + 2, y: e.location.y + 1, z: e.location.z + 2,
        });
        minion.addTag("minizin_aether:summoned");
      }
    } catch (err) { console.warn("[Aether boss] fire minion unavailable: " + err); }
  }
}
function readArena(entity) {
  try {
    const encoded = data(entity, "arena", null);
    if (!encoded) return null;
    const parsed = JSON.parse(encoded);
    if (!parsed || !STAGES[entity.typeId.split(":").pop()]) return null;
    if (![parsed.x, parsed.y, parsed.z].every(Number.isFinite)) return null;
    return parsed;
  } catch { return null; }
}
function* unlockArena(dimension, arena, stage) {
  // Never scan arbitrary regions: tightly bound to the boss's recorded room.
  const size = 20, maxWritesPerTick = 120;
  let attempts = 0, changes = 0;
  for (let x = Math.floor(arena.x) - size; x <= arena.x + size; x++) {
    for (let z = Math.floor(arena.z) - size; z <= arena.z + size; z++) {
      for (let y = Math.floor(arena.y) - 9; y <= arena.y + 17; y++) {
        let block;
        try { block = dimension.getBlock({ x, y, z }); }
        catch { continue; } // Nonloaded chunks are retried from pending record.
        const from = block?.typeId?.replace(D, "");
        if (from in UNLOCK) {
          const dest = UNLOCK[from];
          try {
            block.setPermutation(BlockPermutation.resolve(dest.startsWith("minecraft:")
              ? dest : D + dest));
            changes++;
          } catch { /* missing block permutation */ }
        }
        if (++attempts % maxWritesPerTick === 0) yield;
      }
    }
  }
  console.warn("[Minizin Aether] Unlocked " + stage + " blocks: " + changes);
}
function chestAt(dimension, location, stage) {
  const p = { x: Math.floor(location.x) + 3,
              y: Math.floor(location.y) + 2,
              z: Math.floor(location.z) + 3 };
  try {
    const b = dimension.getBlock(p);
    if (!b) return false;
    // Chest is accessible at arena edge; avoid creating infinite reward
    // inventories on every login using a persistent world clear marker.
    b.setType("minecraft:chest");
    const inventory = b.getComponent("minecraft:inventory");
    const container = inventory?.container;
    if (!container) return false;
    const rewards = DUNGEON_REWARDS[stage] || [];
    const attempts = Math.min(6, rewards.length);
    for (let i = 0; i < attempts; i++) {
      const total = rewards.reduce((a, v) => a + Math.max(1, v.weight), 0);
      let random = Math.random() * total;
      let entry = rewards[0];
      for (const candidate of rewards) {
        random -= Math.max(1, candidate.weight);
        if (random <= 0) { entry = candidate; break; }
      }
      if (!entry) continue;
      const count = entry.count && typeof entry.count === "object" ?
        Math.max(1, Math.floor(entry.count.min + Math.random() *
                 (entry.count.max - entry.count.min + 1))) : Math.max(1, Number(entry.count) || 1);
      try { container.addItem(new ItemStack(entry.name, Math.min(count, 64))); }
      catch (err) { console.warn("[Aether dungeon] reward unavailable: " + entry.name + " " + err); }
    }
    return true;
  } catch (err) {
    console.warn("[Aether dungeon] chest failed: " + String(err));
    return false;
  }
}
function completeDungeonReward(dim, arena, stage, clearedKey, pendingKey) {
  const rewardedKey = D + "dungeon_rewarded:" + arena.cx + ":" + arena.cz;
  if (world.getDynamicProperty(clearedKey) === true) return true;
  // A previously completed chest must never roll its drops twice.
  if (world.getDynamicProperty(rewardedKey) !== true) {
    if (!chestAt(dim, arena, stage)) return false;
    world.setDynamicProperty(rewardedKey, true);
  }
  world.setDynamicProperty(clearedKey, true);
  world.setDynamicProperty(pendingKey, undefined);
  for (const p of world.getAllPlayers()) {
    if (p.dimension.id === dim.id)
      p.sendMessage("§eMasmorra " + stage + " concluída! A recompensa foi desbloqueada.");
  }
  return true;
}
// Recover interrupted reward delivery after a relog or a chunk-load error.
// No scanning unless a player is in the Aether; bounded to the existing
// pending boss records, whose coordinates are integrity-checked.
system.runInterval(() => {
  try {
    const dim = world.getDimension(D + "sky");
    if (!world.getAllPlayers().some(p => p.dimension.id === dim.id)) return;
    for (const key of world.getDynamicPropertyIds()) {
      if (!key.startsWith(D + "dungeon_pending:")) continue;
      const value = world.getDynamicProperty(key);
      if (typeof value !== "string") continue;
      let data;
      try { data = JSON.parse(value); } catch { continue; }
      const a = data?.arena;
      if (!a || !STAGES[Object.keys(STAGES).find(x => STAGES[x].tier === data.stage)] ||
          ![a.x,a.y,a.z,a.cx,a.cz].every(Number.isFinite)) continue;
      if (!world.getAllPlayers().some(p => {
        const v = p.location;
        return p.dimension.id === dim.id &&
          Math.abs(v.x - a.x) < 48 && Math.abs(v.z - a.z) < 48;
      })) continue;
      const cleared = D + "dungeon_cleared:" + a.cx + ":" + a.cz;
      if (world.getDynamicProperty(cleared) !== true) {
        system.runJob(unlockArena(dim, a, data.stage));
        completeDungeonReward(dim, a, data.stage, cleared, key);
      } else {
        world.setDynamicProperty(key, undefined);
      }
    }
  } catch (error) {
    console.warn("[Aether dungeon] pending reward reconciliation: " + String(error));
  }
}, 200);
export function spawnDungeonBoss(dim, tier, location, cx, cz) {
  const name = Object.keys(STAGES).find(key => STAGES[key].tier === tier);
  if (!name) return;
  const key = D + "dungeon_cleared:" + cx + ":" + cz;
  const pending = D + "dungeon_pending:" + cx + ":" + cz;
  if (world.getDynamicProperty(key) === true || world.getDynamicProperty(pending)) return;
  // Allow structure placement to settle before spawning hostile actors.
  system.runTimeout(() => {
    if (world.getDynamicProperty(key) === true) return;
    try {
      const existing = dim.getEntities({ type: D + name, location, maxDistance: 28 });
      if (existing.length) return;
      const entity = dim.spawnEntity(D + name, {
        x: location.x + .5, y: location.y + 3, z: location.z + .5,
      });
      store(entity, "arena", JSON.stringify({ x: location.x, y: location.y,
                                            z: location.z, cx, cz, tier }));
      store(entity, "engaged", false);
    } catch (err) { console.warn("[Aether dungeon] boss spawn: " + String(err)); }
  }, 20);
}
world.afterEvents.playerInteractWithEntity.subscribe(event => {
  if (event.target?.typeId !== D + "valkyrie_queen") return;
  const e = event.target;
  if (data(e, "engaged", false)) return;
  store(e, "engaged", true);
  event.player.sendMessage("§dRainha Valquíria: Demonstre sua coragem!");
});
world.afterEvents.entityHurt.subscribe(event => {
  const mob = event.hurtEntity;
  if (!mob?.typeId?.startsWith(D)) return;
  const type = mob.typeId.slice(D.length);
  const spec = STAGES[type];
  if (!spec) return;
  const attacker = event.damageSource?.damagingEntity;
  let permitted = true;
  if (type === "slider" && attacker?.typeId === "minecraft:player") {
    try {
      const held = attacker.getComponent("minecraft:equippable")?.getEquipment("Mainhand");
      permitted = Boolean(held && (held.typeId.includes("pickaxe") ||
                                   held.typeId === "minecraft:iron_pickaxe"));
    } catch { permitted = false; }
    if (!permitted) attacker.sendMessage("§7O Slider só pode ser ferido com a ferramenta correta!");
  }
  if (type === "valkyrie_queen" && !data(mob, "engaged", false)) permitted = false;
  if (type === "sun_spirit" && Number(data(mob, "frozen_until", 0)) < tickNow()) {
    permitted = false; // frozen by ice crystal to expose vulnerability
    if (attacker?.typeId === "minecraft:player")
      attacker.sendMessage("§bCongele o Espírito do Sol com um projétil de gelo!");
  }
  if (!permitted) {
    // after-event cannot cancel native hurt; restore observed damage.
    const hp = health(mob);
    if (hp) hp.setCurrentValue(Math.min(hp.effectiveMax ?? spec.health,
                                      hp.currentValue + event.damage));
  }
});
world.afterEvents.projectileHitEntity.subscribe(event => {
  const hit = event.getEntityHit?.();
  const victim = hit?.entity;
  if (!victim || victim.typeId !== D + "sun_spirit") return;
  const projectile = event.projectile;
  if (!projectile || !["minecraft:snowball", D + "ice_crystal"].includes(projectile.typeId)) return;
  store(victim, "frozen_until", tickNow() + 100);
  victim.dimension.getPlayers({ location: victim.location, maxDistance: 22 })
    .forEach(p => p.sendMessage("§bO Espírito do Sol foi congelado! Ataque agora."));
});
world.afterEvents.entityDie.subscribe(event => {
  const defeated = event.deadEntity;
  const type = defeated?.typeId?.split(":").pop();
  const stage = STAGES[type]?.tier;
  if (!stage) return;
  const arena = readArena(defeated);
  if (!arena) return;
  const key = D + "dungeon_cleared:" + arena.cx + ":" + arena.cz;
  const pending = D + "dungeon_pending:" + arena.cx + ":" + arena.cz;
  if (world.getDynamicProperty(key) === true ||
      world.getDynamicProperty(pending)) return;
  // Persist first; a crash or unloaded loot chest can now be reconciled.
  world.setDynamicProperty(pending, JSON.stringify({ arena, stage }));
  const dim = defeated.dimension;
  system.runJob(unlockArena(dim, arena, stage));
  system.runTimeout(() => {
    completeDungeonReward(dim, arena, stage, key, pending);
  }, 25);
  ticks.delete(defeated.id);
});
system.runInterval(() => {
  try {
    const dim = world.getDimension(D + "sky");
    for (const key of Object.keys(STAGES)) {
      for (const boss of dim.getEntities({ type: D + key })) {
        const nearby = nearPlayer(boss, STAGES[key].range);
        if (!nearby) continue;
        const s = stateFor(boss);
        if (key === "slider") chargeSlider(boss, nearby.target, s, nearby.distance);
        if (key === "valkyrie_queen") queenCombat(boss, nearby.target, s, nearby.distance);
        if (key === "sun_spirit") sunCombat(boss, nearby.target, s, nearby.distance);
      }
    }
  } catch (error) { console.warn("[Aether boss] runtime: " + String(error)); }
}, 10);
