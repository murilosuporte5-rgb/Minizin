/* Skyroot biome-specific Aether wildlife and non-boss special attacks.
 * Spawning is bounded to loaded cells near players. Source entities/textures
 * and BP behaviors are real; Java spawn weight/conditions are not fully
 * reproducible from the void-dimension Script API.
 */
import { world, system } from "@minecraft/server";
import { AETHER_BIOMES } from "./biome_profiles.js";

const NS = "minizin_aether:";
const CELL = 80;
const MOB_CAP_PER_REGION = 12;
const PER_PLAYER_ENTITY_CAP = 20;
const RESPAWN_INTERVAL = 180;
const attacks = new Map();

const SOURCE_WILDLIFE = {
  skyroot_forest: ["aerbunny", "moa", "phyg", "flying_cow", "sheepuff", "zephyr", "aerwhale", "cockatrice"],
  skyroot_grove: ["aerbunny", "moa", "sheepuff", "aechor_plant", "phyg", "cockatrice"],
  skyroot_meadow: ["sheepuff", "phyg", "flying_cow", "aerbunny", "moa", "zephyr"],
  skyroot_woodland: ["aerbunny", "moa", "valkyrie", "aechor_plant", "cockatrice", "sheepuff"],
};
function seed(x, z) {
  let n = (Math.imul(x, 374761393) ^ Math.imul(z, 668265263)) >>> 0;
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return (n ^ (n >>> 16)) >>> 0;
}
function terrain(x, z, cx, cz) {
  const n = seed(cx, cz), bx = cx * CELL, bz = cz * CELL;
  const dx = x - bx, dz = z - bz;
  const radius = 19 + n % 7;
  const distance = (dx * dx + dz * dz) / (radius * radius);
  if (distance > .78) return undefined;
  const base = 103 + n % 13;
  const undulation = Math.sin((dx + n % 33) * .28) * 2 + Math.cos(dz * .25) * 2;
  return Math.floor(base + undulation - distance * 4);
}
function nearest(entity, reach) {
  let closest, squared = reach * reach;
  for (const player of world.getAllPlayers()) {
    if (player.dimension.id !== entity.dimension.id) continue;
    const a = entity.location, b = player.location;
    const d = (a.x-b.x)**2 + (a.y-b.y)**2 + (a.z-b.z)**2;
    if (d < squared) { squared = d; closest = player; }
  }
  return closest;
}
function canSpawn(dim, x, y, z, airborne) {
  try {
    const at = dim.getBlock({ x, y, z });
    const below = dim.getBlock({ x, y: y - 1, z });
    if (!at || !below || at.typeId !== "minecraft:air") return false;
    return airborne || below.typeId === NS + "aether_grass" ||
      below.typeId === NS + "quicksoil";
  } catch { return false; }
}
function spawnNear(player) {
  const dim = player.dimension;
  const cx = Math.round(player.location.x / CELL);
  const cz = Math.round(player.location.z / CELL);
  const biome = AETHER_BIOMES[seed(cx, cz) % AETHER_BIOMES.length].java_id.split(":")[1];
  const options = SOURCE_WILDLIFE[biome] || [];
  if (!options.length) return;
  const at = { x: cx * CELL, y: player.location.y, z: cz * CELL };
  const existing = dim.getEntities({ location: at, maxDistance: 48,
                                     families: ["minizin_aether"] });
  if (existing.length >= MOB_CAP_PER_REGION) return;
  const playerNear = dim.getEntities({ location: player.location,
                                      maxDistance: 32, families: ["minizin_aether"] });
  if (playerNear.length >= PER_PLAYER_ENTITY_CAP) return;
  for (let i = 0; i < 2; i++) {
    const rnd = seed(cx + i * 77 + Math.floor(system.currentTick / RESPAWN_INTERVAL),
                     cz * 19 + i * 31);
    const choice = options[rnd % options.length];
    const ox = (rnd % 24) - 12, oz = ((rnd >>> 8) % 24) - 12;
    const x = cx * CELL + ox, z = cz * CELL + oz;
    const surface = terrain(x, z, cx, cz);
    if (surface === undefined) continue;
    const flying = ["aerwhale", "zephyr", "phyg", "flying_cow"].includes(choice);
    const y = surface + (flying ? 8 : 2);
    if (!canSpawn(dim, x, y, z, flying)) continue;
    try {
      const e = dim.spawnEntity(NS + choice, { x: x + .5, y, z: z + .5 });
      e.addTag("minizin_aether:wild_generated");
    } catch (err) {
      console.warn("[Minizin Aether] wildlife spawn " + choice + ": " + String(err));
    }
  }
}
function extraAttack(e, victim, key) {
  const now = system.currentTick;
  const last = attacks.get(e.id) || 0;
  if (now - last < 65) return;
  attacks.set(e.id, now);
  try {
    if (key === "aechor_plant") {
      // Rooted poisonous dart attack. Movement remains disabled.
      victim.applyDamage(4, { cause: "entityAttack", damagingEntity: e });
      victim.addEffect("minecraft:poison", 65, { amplifier: 0, showParticles: true });
      e.playAnimation("animation.minizin_aether.aechor_plant.attack");
    } else if (key === "zephyr") {
      // Wind gust distinct from melee.
      const dx = victim.location.x - e.location.x;
      const dz = victim.location.z - e.location.z;
      const dist = Math.max(1, Math.hypot(dx, dz));
      victim.applyImpulse({ x: (dx / dist) * 1.2, y: .35, z: (dz / dist) * 1.2 });
      victim.applyDamage(3, { cause: "entityAttack", damagingEntity: e });
      e.playAnimation("animation.minizin_aether.zephyr.attack");
    } else if (key === "cockatrice") {
      victim.addEffect("minecraft:slowness", 45, { amplifier: 1, showParticles: true });
    }
  } catch (err) {
    console.warn("[Minizin Aether] wildlife special attack: " + err);
  }
}
system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    if (player.dimension.id !== NS + "sky") continue;
    try { spawnNear(player); }
    catch (err) { console.warn("[Minizin Aether] wildlife: " + err); }
  }
}, RESPAWN_INTERVAL);
system.runInterval(() => {
  try {
    const dim = world.getDimension(NS + "sky");
    for (const type of ["zephyr", "aechor_plant", "cockatrice"]) {
      for (const entity of dim.getEntities({ type: NS + type })) {
        const player = nearest(entity, type === "aechor_plant" ? 10 : 12);
        if (player) extraAttack(entity, player, type);
      }
    }
  } catch (err) { console.warn("[Minizin Aether] wildlife combat: " + err); }
}, 20);
