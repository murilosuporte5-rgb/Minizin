import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const catalog=readFileSync(new URL('../bedrock/runtime/aether_altar_catalog.js',import.meta.url),'utf8');
const runtime=readFileSync(new URL('../bedrock/runtime/aether_altar.js',import.meta.url),'utf8');

test('Aether Altar catalog preserves Java repair-time families and fuel burn times',()=>{
  for(const [id,time] of [['minecraft:diamond_sword',1500],['minizin_aether:zanite_sword',750],['minecraft:netherite_sword',2000],['minecraft:wooden_sword',250],['minizin_aether:zanite_ring',500]]){
    assert.match(catalog,new RegExp(id.replace(':','\\:')));assert.match(catalog,new RegExp(`${time}`));
  }
  assert.match(catalog,/ambrosium_shard.*250/);assert.match(catalog,/ambrosium_block.*2500/);
  assert.match(catalog,/AETHER_ALTAR_REPAIRS/);
});

test('Altar runtime persists input, fuel and output while resetting durability only after completion',()=>{
  assert.match(runtime,/minizin:aether_altar_v1/);
  assert.match(runtime,/world\.getAbsoluteTime/);
  assert.match(runtime,/state\.output=encode\(repaired,0\)/);
  assert.match(runtime,/Sem espaço: saída preservada no Altar/);
  assert.match(runtime,/spawnItem/);
});

test('combined and independent builders include Altar runtime',()=>{
  const repair=readFileSync(new URL('../tools/repair_combined_pack.py',import.meta.url),'utf8');
  const expand=readFileSync(new URL('../tools/expand_gameplay.py',import.meta.url),'utf8');
  assert.match(repair,/aether_altar\.js/);assert.match(expand,/aether_altar\.js/);
});
