// Pure, testable scheduling shared by independently packaged creature addons.
export function planAttack(kind, distance, healthFraction, tick, previous = -1000) {
  if (!Number.isFinite(distance) || distance < 0) return null;
  const enraged = healthFraction < 0.5;
  const cooldown = enraged ? 50 : 90;
  if (tick - previous < cooldown) return null;
  if (kind === 'dragon' && distance <= 18)
    return { attack: distance <= 4 ? 'bite' : 'breath', damage: enraged ? 10 : 6, radius: 2.5 };
  if (kind === 'boss' && distance <= 8)
    return { attack: 'slam', damage: enraged ? 12 : 8, radius: enraged ? 5 : 3 };
  if (kind === 'atlatitan' && distance <= 5)
    return { attack: 'stomp', damage: 8, radius: 3 };
  if (kind === 'bluff' && distance <= 4)
    return { attack: 'slam', damage: 5, radius: 2 };
  return null;
}

// Ability selection follows Umvuthi's pinned Java phase/range gates. Timed
// effects and the four source animation clips are handled by creatures.js.
export function planUmvuthiAttack(distance, healthFraction, tick, ready={}) {
  if (!Number.isFinite(distance) || distance < 0 || distance > 24) return null;
  if (healthFraction <= 0.6 && distance <= 10.5 && tick >= (ready.supernova ?? 0))
    return {mode:4,name:'supernova',duration:100,repeat:230};
  if (healthFraction <= 0.6 && tick >= (ready.beam ?? 0))
    return {mode:3,name:'solar_beam',duration:100,repeat:230};
  if (distance < 4)
    return {mode:2,name:'flare',duration:30,repeat:30};
  if (tick >= (ready.sunstrike ?? 0))
    return {mode:1,name:'sun_strike',duration:25,repeat:healthFraction < 0.6 ? 30 : 50};
  return null;
}
