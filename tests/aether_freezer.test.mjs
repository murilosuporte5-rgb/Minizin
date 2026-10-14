import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const catalog=readFileSync(new URL('../bedrock/runtime/aether_freezer_catalog.js',import.meta.url),'utf8');
const runtime=readFileSync(new URL('../bedrock/runtime/aether_freezer.js',import.meta.url),'utf8');

test('Aether Freezer contains all nine Java freezing recipes with original tick durations',()=>{
  for(const [id,time] of [['blue_aercloud_freezing',400],['blue_ice_freezing',500],['crystal_leaves_freezing',500],['high_freezing',500],['ice_from_bucket_freezing',200],['ice_pendant_from_freezing',800],['ice_ring_from_freezing',800],['obsidian_from_bucket_freezing',200],['packed_ice_freezing',300]]){
    assert.match(catalog,new RegExp(`id:"${id}"`));
    assert.match(catalog,new RegExp(`id:"${id}"[^\\n]+time:${time}`));
  }
  assert.equal((catalog.match(/\{id:/g)||[]).length,9);
});

test('Freezer runtime persists slots, completes server-side and preserves bucket remainders',()=>{
  assert.match(runtime,/minizin:aether_freezer_v1/);
  assert.match(runtime,/world\.setDynamicProperty/);
  assert.match(runtime,/world\.getAbsoluteTime/);
  assert.match(runtime,/output_remainder/);
  assert.match(runtime,/spawnItem/);
  assert.match(runtime,/ItemStack\(recipe\.output/);
});

test('Freezer source items are registered by both combined and independent builders',()=>{
  const repair=readFileSync(new URL('../tools/repair_combined_pack.py',import.meta.url),'utf8');
  const expand=readFileSync(new URL('../tools/expand_gameplay.py',import.meta.url),'utf8');
  for(const name of ['skyroot_bucket','skyroot_water_bucket','music_disc_chinchilla','music_disc_high']){
    assert.match(repair,new RegExp(name));
    assert.match(expand,new RegExp(name));
  }
});
