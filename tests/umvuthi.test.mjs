import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../bedrock/runtime/combat.mjs',import.meta.url),'utf8');
const {planUmvuthiAttack}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));

test('Umvuthi retains Java phase gates and distinct attack ranges',()=>{
  assert.equal(planUmvuthiAttack(30,0.2,500),null);
  assert.equal(planUmvuthiAttack(12,0.9,500).name,'sun_strike');
  assert.equal(planUmvuthiAttack(3,0.9,500).name,'flare');
  assert.equal(planUmvuthiAttack(17,0.5,500).name,'solar_beam');
  assert.equal(planUmvuthiAttack(9,0.5,500).name,'supernova');
  assert.equal(planUmvuthiAttack(17,0.5,500,{beam:600,sunstrike:600}),null);
  assert.equal(planUmvuthiAttack(9,0.5,500,{supernova:600,beam:600}).name,'sun_strike');
});
