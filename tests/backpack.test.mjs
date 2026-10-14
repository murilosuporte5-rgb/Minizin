import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../bedrock/runtime/backpack.js',import.meta.url),'utf8').replace(/\r\n/g,'\n')
  .replace(/^import .*;\n/gm,'').replace(/^export /gm,'');
class Stack{
  constructor(type,amount){this.typeId=type;this.amount=amount;this.lore=[];this.props={};this.damage=0;this.enchantments=[];this.destroy=[];this.place=[];this.keepOnDeath=false;this.lockMode='none';}
  getDynamicPropertyIds(){return Object.keys(this.props);}getDynamicProperty(k){return this.props[k];}setDynamicProperty(k,v){this.props[k]=v;}
  getLore(){return this.lore;}setLore(v){this.lore=v;}getCanDestroy(){return this.destroy;}getCanPlaceOn(){return this.place;}
  setCanDestroy(v){this.destroy=v;}setCanPlaceOn(v){this.place=v;}
  getComponent(id){const self=this;if(id==='minecraft:durability')return {get damage(){return self.damage;},set damage(v){self.damage=v;}};
    if(id==='minecraft:enchantable')return {getEnchantments:()=>self.enchantments,addEnchantments:v=>self.enchantments=v};}
}
function harness(){
  const signal={subscribe(){}};const world={beforeEvents:{playerInteractWithBlock:signal,playerInteractWithEntity:signal},afterEvents:{itemUse:signal}};
  return new Function('world','system','ItemStack','EnchantmentTypes','ActionFormData',source+'\nreturn {encode,decode};')
    (world,{},Stack,{get:id=>({id})},class {});
}
test('backpack roundtrip preserves enchantments durability name and dynamic properties',()=>{
  const {encode,decode}=harness();const original=new Stack('minecraft:diamond_sword',1);
  original.nameTag='Original';original.lore=['Linha'];original.damage=37;
  original.enchantments=[{type:{id:'sharpness'},level:3}];original.props={'custom:key':{x:1,y:2,z:3}};
  original.destroy=['minecraft:stone'];original.keepOnDeath=true;
  const encoded=encode(original),restored=decode(encoded);
  assert.deepEqual(encode(restored),encoded);
});
test('nested containers and unsupported hidden data are rejected before deposit',()=>{
  const {encode}=harness();
  for(const id of ['minizin:backpack','minecraft:bundle','minecraft:shulker_box','minecraft:filled_map','minecraft:potion'])
    assert.throws(()=>encode(new Stack(id,1)));
});
