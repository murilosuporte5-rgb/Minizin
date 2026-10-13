// ItemDragonArmor.DragonArmorType ordinal + 1 in the pinned Java source.
export const ARMOR_MATERIALS = ['iron','gold','diamond','silver',
  'dragonsteel_fire','dragonsteel_ice','copper','dragonsteel_lightning'];
export const ARMOR_SLOTS = ['head','neck','body','tail'];
const ARMOR_RATING = [2,1,3,2,4,4,1,4];
export const armorOrdinal = material => Math.max(0,ARMOR_MATERIALS.indexOf(material)+1);
export const armorRating = materials => Math.min(16,ARMOR_SLOTS.reduce((sum,slot)=>{
  const ordinal=armorOrdinal(materials[slot]);
  return sum+(ordinal ? ARMOR_RATING[ordinal-1] : 0);
},0));
