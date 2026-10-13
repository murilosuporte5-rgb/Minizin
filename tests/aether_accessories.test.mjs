import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';

const runtime=readFileSync(new URL('../bedrock/runtime/aether_equipment_v2.js',import.meta.url),'utf8');
const builder=readFileSync(new URL('../tools/repair_combined_pack.py',import.meta.url),'utf8');
const build=fileURLToPath(new URL('../build/',import.meta.url));
const candidates=readdirSync(build).filter(name=>/^combined_all_bosses_final_v\d+$/.test(name))
  .sort((a,b)=>Number(b.match(/v(\d+)$/)[1])-Number(a.match(/v(\d+)$/)[1]));
if(!candidates.length)throw new Error('Build an integrated candidate before running the artifact tests');
const candidate=join(build,candidates[0]);
const catalogSource=readFileSync(join(candidate,'BP/scripts/aether_equipment_catalog.js'),'utf8');
const pickaxe=JSON.parse(readFileSync(join(candidate,'BP/items/aether_equipment/skyroot_pickaxe.json'),'utf8'));
const recipe=JSON.parse(readFileSync(join(candidate,'BP/recipes/aether/skyroot_pickaxe.json'),'utf8'));
const recipeReport=JSON.parse(readFileSync(join(candidate,'FIX_REPORT.json'),'utf8'));
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

test('final Aether tools preserve Java tier components and crafting progression',()=>{
  const item=pickaxe['minecraft:item'].components;
  assert.equal(item['minecraft:durability'].max_durability,59);
  assert.equal(item['minecraft:damage'],1);
  assert.equal(item['minecraft:enchantable'].value,15);
  assert.equal(recipe['minecraft:recipe_shaped'].result.item,'minizin_aether:skyroot_pickaxe');
  assert.equal(recipe['minecraft:recipe_shaped'].key['#'].item,'minizin_aether:skyroot_planks');
  assert.equal(recipe['minecraft:recipe_shaped'].key['/'].item,'minizin_aether:skyroot_stick');
});

test('final Aether recipe report preserves furnace and stonecutter conversions',()=>{
  const written=recipeReport.aether_recipes.written_by_type;
  assert.equal(written['minecraft:stonecutting'],22);
  assert.equal(written['minecraft:smelting'],9);
  assert.equal(written['minecraft:blasting'],9);
  assert.equal(recipeReport.aether_recipes.written,Object.values(written).reduce((sum,n)=>sum+n,0));
  assert.ok(recipeReport.aether_recipes.written>=106);
});

test('repair builder stages original icons and Java durability boundaries',()=>{
  for(const name of ['iron_pendant','ice_pendant','leather_gloves','valkyrie_gloves','invisibility_cloak','golden_feather','shield_of_repulsion'])
    assert.match(builder,new RegExp("['\\\"]"+name+"['\\\"]"));
  assert.match(builder,/'zanite_ring':49/);
  assert.match(builder,/'ice_ring':125/);
  assert.match(builder,/'shield_of_repulsion':512/);
});
