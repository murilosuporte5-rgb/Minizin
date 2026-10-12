/* Minizin Worlds / The Aether (isolated Beta Script API module).
 * Java reference: The-Aether-Team/The-Aether at pinned upstream gitlink.
 * Portals match the original glowstone+water concept; these are not Java's
 * engine/worldgen internals. Uses Bedrock experimental void dimension.
 */
import { world, system, BlockPermutation } from "@minecraft/server";

const SKY_ID = "minizin_aether:sky";
const PORTAL = "minizin_aether:aether_portal";
const RETURN_KEY = "minizin_aether:return";
const CELL_SIZE = 80;
const MAX_PENDING = 8;
const BLOCKS_PER_TICK = 120;
const portalsOnCooldown = new Map();
const pending = [];
const pendingKeys = new Set();
const active = new Set();
let running = false;

function seed(x, z) {
  let n = (Math.imul(x, 374761393) ^ Math.imul(z, 668265263)) >>> 0;
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return (n ^ (n >>> 16)) >>> 0;
}
const cellKey = (x, z) => "minizin_aether:cell:" + x + ":" + z;
const center = (x, z) => ({ x: x * CELL_SIZE, z: z * CELL_SIZE });
function terrain(x, z, cx, cz) {
  const s = seed(cx, cz);
  const at = center(cx, cz);
  const dx = x - at.x;
  const dz = z - at.z;
  const radius = 19 + s % 7;
  const distance = (dx * dx + dz * dz) / (radius * radius);
  if (distance > 1) return null;
  const base = 103 + (s % 13);
  const undulation = Math.sin((dx + s % 33) * .28) * 2 + Math.cos(dz * .25) * 2;
  const surface = Math.floor(base + undulation - distance * 4);
  const depth = Math.max(1, Math.floor((1 - distance) * (8 + (s % 4))));
  return { surface, depth, distance };
}
function getKey(pos) { return Math.floor(pos.x) + ":" + Math.floor(pos.y) + ":" + Math.floor(pos.z); }

system.beforeEvents.startup.subscribe((event) => {
  // Exactly one custom dimension; creating another dimension ID would alter
  // saved-world identity and should be done only by a migration.
  event.dimensionRegistry.registerCustomDimension(SKY_ID);
});

function isBlock(dimension, pos, typeId) {
  try { return dimension.getBlock(pos)?.typeId === typeId; }
  catch { return false; }
}
function findGlowstoneFrame(dimension, touched) {
  // Java-inspired frame: outside is 4 wide x 5 tall, inside is 2 x 3.
  // This enumerates both horizontal axes and all possible touched frame tiles.
  for (const axis of ["x", "z"]) {
    for (let horiz = 0; horiz < 4; horiz++) {
      for (let vert = 0; vert < 5; vert++) {
        const base = {
          x: touched.x - (axis === "x" ? horiz : 0),
          y: touched.y - vert,
          z: touched.z - (axis === "z" ? horiz : 0),
        };
        const tile = (h, v) => ({
          x: base.x + (axis === "x" ? h : 0),
          y: base.y + v,
          z: base.z + (axis === "z" ? h : 0),
        });
        let valid = true;
        for (let h = 0; h < 4 && valid; h++) {
          for (let v = 0; v < 5; v++) {
            const outer = h === 0 || h === 3 || v === 0 || v === 4;
            const block = dimension.getBlock(tile(h, v));
            const allowed = outer ? block?.typeId === "minecraft:glowstone" :
              ["minecraft:air", PORTAL, "minecraft:water", "minecraft:flowing_water"].includes(block?.typeId);
            if (!allowed) { valid = false; break; }
          }
        }
        if (valid) return { tile, axis };
      }
    }
  }
  return null;
}
function activateFrame(dimension, frame) {
  const portal = BlockPermutation.resolve(PORTAL, { "minizin_aether:axis": frame.axis });
  for (let h = 1; h < 3; h++) {
    for (let v = 1; v < 4; v++) {
      dimension.getBlock(frame.tile(h, v))?.setPermutation(portal);
    }
  }
}
function heldWater(event) {
  return event.itemStack?.typeId === "minecraft:water_bucket";
}
world.afterEvents.playerInteractWithBlock.subscribe((event) => {
  try {
    if (!heldWater(event) || event.block?.typeId !== "minecraft:glowstone") return;
    const pos = event.block.location;
    const frame = findGlowstoneFrame(event.block.dimension, pos);
    if (!frame) return;
    activateFrame(event.block.dimension, frame);
    event.player.sendMessage("§bPortal do Aether ativado. Atravesse a superfície azul.");
  } catch (error) {
    event.player?.sendMessage("§cErro ao ativar portal: " + String(error));
  }
});

const permCache = new Map();
function set(dim, x, y, z, id) {
  let perm = permCache.get(id);
  if (!perm) {
    perm = BlockPermutation.resolve(id);
    permCache.set(id, perm);
  }
  const block = dim.getBlock({ x, y, z });
  if (block && block.typeId !== id) block.setPermutation(perm);
}
async function yieldBudget(counter) {
  if (counter % BLOCKS_PER_TICK === 0) {
    await new Promise((resolve) => system.runTimeout(resolve, 1));
  }
}
function addTree(dim, x, y, z, s, giant = false) {
  const height = giant ? 8 + (s % 4) : 5 + (s % 3);
  const wood = giant ? "minizin_aether:golden_oak_log" : "minizin_aether:skyroot_log";
  const leaf = giant ? "minizin_aether:golden_oak_leaves" : "minizin_aether:skyroot_leaves";
  for (let h = 0; h < height; h++) set(dim, x, y + h, z, wood);
  const r = giant ? 3 : 2;
  for (let dx = -r; dx <= r; dx++) {
    for (let dz = -r; dz <= r; dz++) {
      for (let dy = -2; dy <= 1; dy++) {
        if (dx * dx + dz * dz + dy * dy > r * r + 2) continue;
        const p = { x: x + dx, y: y + height + dy, z: z + dz };
        if (isBlock(dim, p, "minecraft:air")) set(dim, p.x, p.y, p.z, leaf);
      }
    }
  }
}
function placeOriginalDungeon(dim, x, y, z, cx, cz) {
  // The .mcstructure files are converted from pinned Java templates, not
  // invented rooms. No claim of boss AI / generation algorithm equivalence.
  const family = ["bronze", "silver", "gold"][seed(cx, cz) % 3];
  const preferred = [
    "minizin_aether:" + family + "_dungeon/boss_room",
    "minizin_aether:" + family + "_dungeon/entrance",
    "minizin_aether:" + family + "_dungeon/skeleton",
  ];
  const manager = world.structureManager;
  if (!manager || !manager.getPackStructureIds) return false;
  try {
    const known = new Set(manager.getPackStructureIds());
    const chosen = preferred.find(id => known.has(id));
    if (!chosen) return false;
    // Structure API queues placement across unloaded chunks. Coordinates are
    // anchored at the cell center; positional parity with Java is unverified.
    manager.place(chosen, dim, { x: x - 12, y, z: z - 12 });
    console.warn("[Minizin Aether] Original template placed: " + chosen);
    return true;
  } catch (error) {
    console.warn("[Minizin Aether] Original dungeon placement failed: " + String(error));
    return false;
  }
}
function addTemple(dim, x, y, z) {
  // Deterministic small dungeon room, not a copy of the Java Bronze/Silver/Gold dungeon.
  for (let dx = -4; dx <= 4; dx++) {
    for (let dz = -4; dz <= 4; dz++) {
      set(dim, x + dx, y, z + dz, "minizin_aether:holystone_bricks");
      for (let h = 1; h <= 5; h++) {
        const wall = Math.abs(dx) === 4 || Math.abs(dz) === 4 || h === 5;
        if (wall) set(dim, x + dx, y + h, z + dz,
                      h === 5 ? "minizin_aether:holystone_bricks" : "minizin_aether:holystone");
        else set(dim, x + dx, y + h, z + dz, "minecraft:air");
      }
    }
  }
  // Doorway and light, deliberately no fabricated boss behavior.
  for (let h = 1; h <= 3; h++) set(dim, x, y + h, z - 4, "minecraft:air");
  set(dim, x, y + 1, z + 2, "minecraft:chest");
  set(dim, x, y + 2, z + 2, "minecraft:glowstone");
}
function addExitFrame(dim, y) {
  const base = { x: 7, y: y + 1, z: -7 };
  const tile = (h, v) => ({ x: base.x + h, y: base.y + v, z: base.z });
  for (let h = 0; h < 4; h++) {
    for (let v = 0; v < 5; v++) {
      const edge = h === 0 || h === 3 || v === 0 || v === 4;
      if (edge) set(dim, base.x + h, base.y + v, base.z, "minecraft:glowstone");
    }
  }
  activateFrame(dim, { tile, axis: "x" });
}
async function generateCell(cx, cz) {
  const key = cellKey(cx, cz);
  if (world.getDynamicProperty(key) === true) return;
  const dim = world.getDimension(SKY_ID);
  const c = center(cx, cz);
  const s = seed(cx, cz);
  const radius = 19 + s % 7;
  const area = "minizin_aether_" + (cx + 9999) + "_" + (cz + 9999);
  if (!world.tickingAreaManager) throw new Error("Beta tickingAreaManager unavailable");
  // Preload before touching blocks in a dimension with an empty generator.
  await world.tickingAreaManager.createTickingArea(area, {
    dimension: dim,
    from: { x: c.x - radius - 2, y: 70, z: c.z - radius - 2 },
    to: { x: c.x + radius + 2, y: 145, z: c.z + radius + 2 },
  });
  let writes = 0;
  try {
    for (let dx = -radius; dx <= radius; dx++) {
      for (let dz = -radius; dz <= radius; dz++) {
        const x = c.x + dx, z = c.z + dz;
        const t = terrain(x, z, cx, cz);
        if (!t) continue;
        for (let h = t.surface - t.depth; h <= t.surface; h++) {
          const ore = (seed(x * 17 + h, z * 19) % 37) === 0;
          const id = h === t.surface ? "minizin_aether:aether_grass" :
            h > t.surface - 3 ? "minizin_aether:aether_dirt" :
            ore ? (seed(x, z + h) % 3 ? "minizin_aether:ambrosium_ore" : "minizin_aether:zanite_ore") :
            "minizin_aether:holystone";
          set(dim, x, h, z, id);
          await yieldBudget(++writes);
        }
      }
    }
    // Reproducible placement based on cell coordinates, never overwrite the spawn pad.
    const places = [[-9, -2], [10, 9], [-4, 10], [12, -8]];
    for (let i = 0; i < places.length; i++) {
      const [dx, dz] = places[i];
      const t = terrain(c.x + dx, c.z + dz, cx, cz);
      if (!t || t.distance > .65) continue;
      addTree(dim, c.x + dx, t.surface + 1, c.z + dz,
              seed(cx * 11 + i, cz * 29), i === 0 && s % 4 === 0);
      await yieldBudget(++writes);
    }
    if (cx === 0 && cz === 0) {
      // Landing is clear even in survival; the exit portal stands nearby.
      const pad = terrain(0, 0, 0, 0).surface;
      for (let x = -2; x <= 2; x++) for (let z = -2; z <= 2; z++)
        set(dim, x, pad, z, "minizin_aether:aether_grass");
      for (let y = pad + 1; y <= pad + 4; y++) for (let x = -2; x <= 2; x++)
        for (let z = -2; z <= 2; z++) set(dim, x, y, z, "minecraft:air");
      const exitHeight = terrain(7, -7, 0, 0)?.surface ?? pad;
      addExitFrame(dim, exitHeight);
    } else if (s % 5 === 0) {
      const t = terrain(c.x, c.z, cx, cz);
      // Prefer a converted original template when available. The simplified
      // room is retained only as an explicit fallback, never a Java replica.
      if (!placeOriginalDungeon(dim, c.x, t.surface + 1, c.z, cx, cz))
        addTemple(dim, c.x, t.surface + 1, c.z);
    }
    // Persist only on complete success; interrupted cells regenerate idempotently.
    world.setDynamicProperty(key, true);
  } finally {
    world.tickingAreaManager.removeTickingArea(area);
  }
}
function enqueue(cx, cz) {
  const key = cellKey(cx, cz);
  if (world.getDynamicProperty(key) === true || pendingKeys.has(key) || active.has(key)) return;
  if (pending.length >= MAX_PENDING) return;
  pending.push([cx, cz]);
  pendingKeys.add(key);
  if (!running) system.run(() => { void drain(); });
}
async function drain() {
  if (running) return;
  running = true;
  try {
    while (pending.length) {
      const [cx, cz] = pending.shift();
      const k = cellKey(cx, cz);
      pendingKeys.delete(k);
      active.add(k);
      try { await generateCell(cx, cz); }
      catch (err) {
        console.warn("[Minizin Aether] worldgen " + k + ": " + String(err));
        // Do not spin on an unsupported API or unloaded destination.
      } finally { active.delete(k); }
    }
  } finally { running = false; }
}
function portalTouch(player) {
  const p = player.location;
  for (const oy of [0, 1]) {
    const pos = { x: Math.floor(p.x), y: Math.floor(p.y) + oy, z: Math.floor(p.z) };
    if (isBlock(player.dimension, pos, PORTAL)) return true;
  }
  return false;
}
function readyToTravel(player) {
  const last = portalsOnCooldown.get(player.id) || -99999;
  if (system.currentTick - last < 100) return false;
  portalsOnCooldown.set(player.id, system.currentTick);
  return true;
}
async function visitAether(player) {
  const p = player.location;
  player.setDynamicProperty(RETURN_KEY, JSON.stringify({
    x: Math.floor(p.x), y: Math.floor(p.y), z: Math.floor(p.z),
  }));
  player.sendMessage("§bGerando ilha inicial do Aether...");
  // Even if initial island is already stored, preload arrival before teleport.
  await generateCell(0, 0);
  const dim = world.getDimension(SKY_ID);
  const y = terrain(0, 0, 0, 0).surface + 2;
  const a = "minizin_aether_arrival";
  await world.tickingAreaManager.createTickingArea(a, {
    dimension: dim, from: { x: -4, y: y - 6, z: -4 },
    to: { x: 4, y: y + 8, z: 4 },
  });
  try { player.teleport({ x: .5, y, z: .5 }, { dimension: dim }); }
  finally { world.tickingAreaManager.removeTickingArea(a); }
}
function returnOverworld(player) {
  let target;
  try { target = JSON.parse(player.getDynamicProperty(RETURN_KEY) || "null"); }
  catch { target = null; }
  if (!target || ![target.x, target.y, target.z].every(Number.isFinite)) {
    player.sendMessage("§cPosição de retorno indisponível; use um portal de entrada válido.");
    return;
  }
  player.teleport({ x: target.x + .5, y: target.y + 1, z: target.z + .5 },
                  { dimension: world.getDimension("minecraft:overworld") });
}
world.afterEvents.worldLoad.subscribe(() => {
  world.sendMessage("§bMinizin The Aether: portal 4x5 de glowstone + balde de água. Beta APIs necessário.");
  enqueue(0, 0);
});
system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    try {
      if (player.dimension.id === SKY_ID) {
        if (player.location.y < 10) {
          if (readyToTravel(player)) returnOverworld(player);
          continue;
        }
        // Only build as players explore; serialized generation and capped queue.
        const cx = Math.round(player.location.x / CELL_SIZE);
        const cz = Math.round(player.location.z / CELL_SIZE);
        enqueue(cx, cz);
        for (const [dx, dz] of [[-1, 0], [1, 0], [0, -1], [0, 1]])
          enqueue(cx + dx, cz + dz);
      }
      if (!portalTouch(player) || !readyToTravel(player)) continue;
      if (player.dimension.id === SKY_ID) returnOverworld(player);
      else if (player.dimension.id === "minecraft:overworld") {
        void visitAether(player).catch((error) => {
          player.sendMessage("§cAether indisponível: " + String(error));
          console.warn("[Minizin Aether] teleport: " + String(error));
        });
      }
    } catch (error) {
      console.warn("[Minizin Aether] tick: " + String(error));
    }
  }
}, 12);
