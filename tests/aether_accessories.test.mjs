import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const runtime=readFileSync(new URL('../bedrock/runtime/aether_equipment_v2.js',import.meta.url),'utf8');
const builder=readFileSync(new URL('../tools/repair_combined_pack.py',import.meta.url),'utf8');
const catalogSource=readFileSync(new URL('../build/combined_all_bosses_final_v22/BP/scripts/aether_equipment_catalog.js',import.meta.url),'utf8');
const catalog=JSON.parse(catalogSource.replace(/^export const EQUIPMENT = /,'').replace(/;\s*$/,''));

test('Aether virtual accessory menu matches Java slot categories and counts',()=>{
  assert.match(runtime,/aether_accessories_v2/);
  assert.match(runtime,/\{id:"ring",label:"Anéis",count:2\}/);
  assert.match(runtime,/\{id:"pendant",label:"Pendants",count:1\}/);
  assert.match(runtime,/\{id:"gloves",label:"Luvas",count:1\}/);
  assert.match(runtime,/\{id:"cape",label:"Capas",count:1\}/);
  assert.match(runtime,/\{id:"shield",label:"Escudo",count:1\}/);
  assert.match(runtime,/\{id:"accessory",label:"Acessórios",count:2\}/);
});

test('Aether accessories are usable without the native offhand',()=>{
  assert.match(runtime,/world\.afterEvents\.itemUse/);
  assert.match(runtime,/independentes da mão secundária/);
  assert.match(runtime,/LEGACY_SLOT_KEY/);
  assert.match(runtime,/EquipmentSlot\.Offhand/);
});

test('final Aether catalog contains original accessory families',()=>{
  const accessories=Object.entries(catalog).filter(([,value])=>value.accessory);
  assert.equal(accessories.length,32);
  for(const family of ['ring','pendant','gloves','cape','shield','accessory'])
    assert.ok(accessories.some(([,value])=>value.slot===family),family);
  for(const id of ['minizin_aether:ice_ring','minizin_aether:ice_pendant','minizin_aether:invisibility_cloak','minizin_aether:shield_of_repulsion'])
    assert.equal(catalog[id].accessory,true,id);
});

test('repair builder stages original icons and Java durability boundaries',()=>{
  for(const name of ['iron_pendant','ice_pendant','leather_gloves','valkyrie_gloves','invisibility_cloak','golden_feather','shield_of_repulsion'])
    assert.match(builder,new RegExp("['\\\"]"+name+"['\\\"]"));
  assert.match(builder,/'zanite_ring':49/);
  assert.match(builder,/'ice_ring':125/);
  assert.match(builder,/'shield_of_repulsion':512/);
});
