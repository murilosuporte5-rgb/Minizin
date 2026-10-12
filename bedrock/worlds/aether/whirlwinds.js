/* Aether Whirlwinds: the original WhirlwindRenderer has NO ModelPart
 * geometry; Java displays procedural particles. This Bedrock adaptation
 * deliberately uses particles + genuine whirlpool force (not a dummy cube).
 * Java source: AbstractWhirlwind, EvilWhirlwind, PassiveWhirlwind.
 */
import { world, system } from "@minecraft/server";

const SKY = "minizin_aether:sky";
const STYLES = {
  whirlwind: { lifetime: 512, force: 0.30, damage: 0 },
  evil_whirlwind: { lifetime: 256, force: 0.46, damage: 2 },
};
const lastHit = new Map();
function animateWhirlwind(dim, entity, style, now) {
  const p = entity.location;
  // Original renderer uses airborne swirling particle columns. Emulate
  // circulation from the real mob center, not from a generated block cube.
  for (let i = 0; i < 6; ++i) {
    const angle = now * .19 + i * Math.PI / 3;
    const height = .3 + (i % 5) * .26;
    const radius = .55 + (i % 2) * .25;
    const particle = {
      x: p.x + Math.sin(angle) * radius,
      y: p.y + height,
      z: p.z + Math.cos(angle) * radius,
    };
    try {
      dim.spawnParticle(style.damage ? "minecraft:basic_flame_particle" :
                         "minecraft:basic_smoke_particle", particle);
    } catch (error) {
      // Particle ID support differs by Bedrock version: movement continues.
      if (now % 300 === 0)
        console.warn("[Aether Whirlwind] particle unsupported: " + error);
    }
  }
}
function pullNearby(dim, entity, style, now) {
  const at = entity.location;
  for (const p of world.getAllPlayers()) {
    if (p.dimension.id !== dim.id) continue;
    const loc = p.location, dx = loc.x - at.x, dz = loc.z - at.z;
    const distance = Math.max(.15, Math.hypot(dx, dz));
    if (distance > 2.8 || Math.abs(loc.y - at.y) > 3) continue;
    // Tangential circulation and lift derived from the Java whirlwind idea.
    const strength = style.force / Math.max(.65, distance);
    try {
      p.applyImpulse({
        x: (-dz / distance) * strength - dx * .025,
        y: .13 + strength * .38,
        z: (dx / distance) * strength - dz * .025,
      });
      if (style.damage && now - (lastHit.get(p.id) || -999) > 40) {
        p.applyDamage(style.damage, {
          cause: "entityAttack", damagingEntity: entity,
        });
        lastHit.set(p.id, now);
      }
    } catch (error) {
      console.warn("[Aether Whirlwind] vortex force: " + error);
    }
  }
}
system.runInterval(() => {
  let dim;
  try { dim = world.getDimension(SKY); }
  catch { return; }
  const now = system.currentTick;
  for (const [mob, style] of Object.entries(STYLES)) {
    for (const entity of dim.getEntities({ type: "minizin_aether:" + mob })) {
      try {
        let birth = entity.getDynamicProperty("minizin_aether:birth");
        if (typeof birth !== "number") {
          birth = now;
          entity.setDynamicProperty("minizin_aether:birth", birth);
        }
        if (now - birth > style.lifetime) {
          entity.remove();
          continue;
        }
        // Bound rendering to players near the actor: Android budget.
        if (dim.getPlayers({ location: entity.location, maxDistance: 24 }).length) {
          animateWhirlwind(dim, entity, style, now);
          pullNearby(dim, entity, style, now);
        }
      } catch (error) {
        console.warn("[Aether Whirlwind] runtime: " + String(error));
      }
    }
  }
}, 5);
