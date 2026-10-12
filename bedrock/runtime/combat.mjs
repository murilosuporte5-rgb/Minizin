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
