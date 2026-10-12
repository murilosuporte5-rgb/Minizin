/* Bedrock-adapted BoP vegetation overlay, separate from custom-biome JSON.
 * Biomes O' Plenty has custom noise and climate rules in Java. The stable
 * Bedrock add-on API cannot replace its overworld biome router. This module
 * places source-textured plants and trees in deterministic regions on loaded
 * vanilla terrain without claiming native biome replacement.
 */
import { BlockPermutation, system, world } from "@minecraft/server";
import { NATIVE_BOP } from "./native_biomes.js";

const NS = "minizin_bop";
const CELL = 48;                 // small enough to operate on loaded ground
const PLACEMENTS_PER_TICK = 16; // mobile performance cap
const INTERVAL_TICKS = 100;
const MAX_PENDING = 3;
const pending = [];
const scheduled = new Set();
let running = false;

const SPEC = [
  { biome: "lavender_field", log: null, leaves: null, flower: "lavender", trees: 0, plants: 22 },
  { biome: "mystic_grove", log: "magic_log", leaves: "magic_leaves", flower: "glowflower", trees: 4, plants: 8 },
  { biome: "redwood_forest", log: "redwood_log", leaves: "redwood_leaves", flower: null, trees: 5, plants: 0 },
  { biome: "ominous_woods", log: "umbran_log", leaves: "umbran_leaves", flower: null, trees: 6, plants: 0 },
  { biome: "coniferous_forest", log: "fir_log", leaves: "fir_leaves", flower: null, trees: 6, plants: 0 },
  { biome: "maple_woods", log: "maple_log", leaves: "maple_leaves", flower: null, trees: 5, plants: 0 },
  { biome: "jade_cliffs", log: "jacaranda_log", leaves: "jacaranda_leaves", flower: null, trees: 4, plants: 0 },
  { biome: "tropics", log: "palm_log", leaves: "palm_leaves", flower: null, trees: 4, plants: 0 },
  { biome: "highland", log: "pine_log", leaves: "pine_leaves", flower: null, trees: 4, plants: 0 },
];
const permutations = new Map();
function block(dim, p) {
  try { return dim.getBlock(p); }
  catch { return undefined; }
}
function set(dim, p, identifier) {
  const current = block(dim, p);
  if (!current) return false;
  if (current.typeId === identifier) return true;
  let perm = permutations.get(identifier);
  if (!perm) {
    perm = BlockPermutation.resolve(identifier);
    permutations.set(identifier, perm);
  }
  current.setPermutation(perm);
  return true;
}
function noise(x, z) {
  let n = Math.imul(x, 0x9e3779b1) ^ Math.imul(z, 0x85ebca77);
  n = Math.imul(n ^ (n >>> 16), 0x7feb352d);
  return (n ^ (n >>> 15)) >>> 0;
}
function zoneId(cx, cz) { return NS + ":vegetation:v1:" + cx + ":" + cz; }
function pick(cx, cz) { return SPEC[noise(cx, cz) % SPEC.length]; }
function canGrowOn(id) {
  return ["minecraft:grass_block", "minecraft:dirt", "minecraft:podzol"].includes(id);
}
function surface(dim, x, z, referenceY) {
  // Limited height search instead of scanning 384 layers per placement.
  const hi = Math.min(315, Math.floor(referenceY) + 20);
  const low = Math.max(-62, Math.floor(referenceY) - 36);
  for (let y = hi; y >= low; --y) {
    const top = block(dim, { x, y: y + 1, z });
    const ground = block(dim, { x, y, z });
    if (!ground || !top) return null; // unloaded cells are not writable
    if (!["minecraft:air", "minecraft:tallgrass", "minecraft:short_grass"].includes(top.typeId)) {
      if (ground.typeId === "minecraft:air") continue;
      return null;  // never excavate builds, water, or existing terrain
    }
    if (canGrowOn(ground.typeId)) return y;
    if (ground.typeId !== "minecraft:air") return null;
  }
  return null;
}
function treeClear(dim, x, y, z, height, radius) {
  for (let h = 0; h <= height + 2; ++h) {
    const b = block(dim, { x, y: y + h, z });
    if (!b || b.typeId !== "minecraft:air") return false;
  }
  for (let dx = -radius; dx <= radius; ++dx) for (let dz = -radius; dz <= radius; ++dz) {
    const b = block(dim, { x: x + dx, y: y + height - 1, z: z + dz });
    if (!b || b.typeId !== "minecraft:air") return false;
  }
  return true;
}
function growTree(dim, x, y, z, height, radius, spec) {
  for (let h = 0; h < height; ++h)
    set(dim, { x, y: y + h, z }, NS + ":" + spec.log);
  for (let dy = -2; dy <= 2; ++dy) {
    for (let dx = -radius; dx <= radius; ++dx) {
      for (let dz = -radius; dz <= radius; ++dz) {
        const d = dx * dx + dz * dz + dy * dy;
        if (d > radius * radius + 2) continue;
        const p = { x: x + dx, y: y + height + dy, z: z + dz };
        if (block(dim, p)?.typeId === "minecraft:air")
          set(dim, p, NS + ":" + spec.leaves);
      }
    }
  }
}
function flowerClear(dim, x, y, z) {
  return block(dim, { x, y, z })?.typeId === "minecraft:air";
}
async function generate(cx, cz, referenceY, dim) {
  const key = zoneId(cx, cz);
  if (world.getDynamicProperty(key) === true) return;
  const ox = cx * CELL, oz = cz * CELL;
  // Use the actual native biome ID, NOT a fictional cell-index biome.
  let native;
  try {
    const biome = dim.getBiome({ x: ox + Math.floor(CELL / 2),
                                 y: referenceY, z: oz + Math.floor(CELL / 2) });
    native = NATIVE_BOP[biome.id];
  } catch { return; }
  if (!native || native.dimension !== "minecraft:overworld") return;
  const spec = {
    biome: "native_" + (native.tree || native.flower || "unported"),
    log: native.tree ? native.tree + "_log" : null,
    leaves: native.tree ? native.tree + "_leaves" : null,
    flower: native.flower,
    trees: native.tree ? 4 : 0,
    plants: native.flower ? 10 : 0,
  };
  if (spec.trees === 0 && spec.plants === 0) return;
  let attempts = 0, writes = 0, observed = 0;
  const total = spec.trees + spec.plants;
  for (let n = 0; n < total; n++) {
    // Keep patches toward cell center and inside the player's loaded chunks.
    const s = noise(cx * 97 + n, cz * 131 - n);
    const x = ox + 8 + (s % (CELL - 16));
    const z = oz + 8 + ((s >>> 8) % (CELL - 16));
    if (!dim.isChunkLoaded({ x, y: Math.floor(referenceY), z })) continue;
    observed++;
    const floor = surface(dim, x, z, referenceY);
    if (floor === null) continue;
    const y = floor + 1;
    if (n < spec.trees) {
      const height = spec.biome === "redwood_forest" ? 12 + (s % 5) : 5 + (s % 4);
      const radius = spec.biome === "redwood_forest" ? 3 : 2;
      if (treeClear(dim, x, y, z, height, radius)) {
        growTree(dim, x, y, z, height, radius, spec);
        writes++;
      }
    } else if (spec.flower && flowerClear(dim, x, y, z)) {
      set(dim, { x, y, z }, NS + ":" + spec.flower);
      writes++;
    }
    if (++attempts % PLACEMENTS_PER_TICK === 0)
      await new Promise(resolve => system.runTimeout(resolve, 1));
  }
  // Do not permanently commit empty cells that were outside render distance.
  // The player may revisit them with a larger simulation radius later.
  if (observed < Math.max(1, Math.floor(total * .6))) {
    console.warn("[Minizin BOP] Deferred region " + key + " (chunks unloaded)");
    return;
  }
  world.setDynamicProperty(key, true);
  console.warn("[Minizin BOP] Region " + key + " (" + spec.biome + ") " + writes + " features.");
}
function schedule(dim, cx, cz, referenceY) {
  const key = zoneId(cx, cz);
  if (world.getDynamicProperty(key) === true || scheduled.has(key) || pending.length >= MAX_PENDING) return;
  scheduled.add(key);
  pending.push({ dim, cx, cz, referenceY });
  if (!running) system.run(() => { void drain(); });
}
async function drain() {
  if (running) return;
  running = true;
  try {
    while (pending.length) {
      const { dim, cx, cz, referenceY } = pending.shift();
      const key = zoneId(cx, cz);
      try { await generate(cx, cz, referenceY, dim); }
      catch (error) { console.warn("[Minizin BOP] Region failed, retry later: " + String(error)); }
      finally { scheduled.delete(key); }
    }
  } finally { running = false; }
}
system.runInterval(() => {
  for (const p of world.getAllPlayers()) {
    if (p.dimension.id !== "minecraft:overworld") continue;
    try {
      const biome = p.dimension.getBiome(p.location);
      if (!NATIVE_BOP[biome.id]) continue;
    } catch { continue; }
    const cx = Math.floor(p.location.x / CELL), cz = Math.floor(p.location.z / CELL);
    schedule(p.dimension, cx, cz, p.location.y);
  }
}, INTERVAL_TICKS);
