import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const catalog=readFileSync(new URL('../bedrock/runtime/aether_incubator_catalog.js',import.meta.url),'utf8');
const runtime=readFileSync(new URL('../bedrock/runtime/aether_incubator.js',import.meta.url),'utf8');

test('Aether Incubator preserves the three Java Moa incubation recipes and fuel times',()=>{
  for(const type of ['black','blue','white']) assert.match(catalog,new RegExp(`minizin_aether:${type}_moa_egg`));
  assert.equal((catalog.match(/id:/g)||[]).length,3);
  assert.match(catalog,/time:1000/);
  assert.match(catalog,/ambrosium_torch.*500/);
});

test('Incubator runtime persists two slots and spawns a configured baby Moa only after completion',()=>{
  assert.match(runtime,/minizin:aether_incubator_v1/);
  assert.match(runtime,/world\.getAbsoluteTime/);
  assert.match(runtime,/spawnEntity\("minizin_aether:moa"/);
  assert.match(runtime,/minizin:moa_type/);
  assert.match(runtime,/minizin:moa_player_grown/);
  assert.match(runtime,/world\.setDynamicProperty/);
});

test('combined and independent builders include the Incubator runtime and source item icons',()=>{
  const repair=readFileSync(new URL('../tools/repair_combined_pack.py',import.meta.url),'utf8');
  const expand=readFileSync(new URL('../tools/expand_gameplay.py',import.meta.url),'utf8');
  for(const name of ['black_moa_egg','blue_moa_egg','white_moa_egg','ambrosium_torch']){
    assert.match(repair,new RegExp(name)); assert.match(expand,new RegExp(name));
  }
  assert.match(repair,/aether_incubator\.js/);assert.match(expand,/aether_incubator\.js/);
});
