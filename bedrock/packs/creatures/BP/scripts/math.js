// Pure deterministic helpers; also exercised by tests/creatures_logic.test.mjs.
export function dragonStage(days) {
  return days >= 100 ? 5 : days >= 75 ? 4 : days >= 50 ? 3 : days >= 25 ? 2 : 1;
}
export function ignisPhase(health, maxHealth) {
  if (!(maxHealth > 0)) return 0;
  return health <= maxHealth / 3 ? 2 : health <= maxHealth * 2 / 3 ? 1 : 0;
}
export function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
}
export function direction(a, b) {
  const dx = b.x - a.x, dz = b.z - a.z;
  const n = Math.max(0.001, Math.hypot(dx, dz));
  return {x: dx / n, z: dz / n};
}
export function nearSegment(point, from, to, radius) {
  const dx=to.x-from.x, dz=to.z-from.z;
  const t=Math.max(0, Math.min(1, ((point.x-from.x)*dx+(point.z-from.z)*dz)/Math.max(0.001, dx*dx+dz*dz)));
  const px=from.x+t*dx, pz=from.z+t*dz;
  return Math.hypot(point.x-px, point.z-pz)<=radius;
}
