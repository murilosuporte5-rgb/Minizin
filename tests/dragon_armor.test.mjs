import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../bedrock/runtime/dragon_armor.js',import.meta.url),'utf8');
const {ARMOR_MATERIALS,ARMOR_SLOTS,armorOrdinal,armorRating}=await import(
  'data:text/javascript;base64,'+Buffer.from(source).toString('base64'));

test('Java armor ordinals map to all 32 slot pieces and a bounded protection value',()=>{
  assert.deepEqual(ARMOR_MATERIALS,['iron','gold','diamond','silver',
    'dragonsteel_fire','dragonsteel_ice','copper','dragonsteel_lightning']);
  assert.deepEqual(ARMOR_SLOTS,['head','neck','body','tail']);
  assert.equal(armorOrdinal('dragonsteel_fire'),5);
  assert.equal(armorOrdinal('copper'),7);
  assert.equal(armorOrdinal('absent'),0);
  assert.equal(armorRating({}),0);
  assert.equal(armorRating({head:'iron',neck:'copper'}),3);
  assert.equal(armorRating(Object.fromEntries(ARMOR_SLOTS.map(slot=>[slot,'dragonsteel_fire']))),16);
});
