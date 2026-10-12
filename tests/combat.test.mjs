import test from 'node:test';
import assert from 'node:assert/strict';
import {planAttack} from '../bedrock/runtime/combat.mjs';

test('cooldown blocks damage on consecutive ticks',()=>{
  assert.equal(planAttack('dragon',10,1,100,95),null);
  assert.equal(planAttack('dragon',10,1,190,100).attack,'breath');
});
test('boss phase changes cooldown, radius and damage',()=>{
  assert.equal(planAttack('boss',4,1,60,0),null);
  const rage=planAttack('boss',4,0.4,60,0);
  assert.equal(rage.radius,5);assert.equal(rage.damage,12);
});
test('attacks respect range and invalid distances',()=>{
  for(const distance of [-1,NaN,Infinity,50])assert.equal(planAttack('dragon',distance,1,100),null);
  assert.equal(planAttack('atlatitan',6,1,100),null);
  assert.equal(planAttack('dragon',2,1,100).attack,'bite');
});
