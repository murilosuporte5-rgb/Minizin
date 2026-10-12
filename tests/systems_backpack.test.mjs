import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const source=readFileSync(new URL("../bedrock/packs/sophisticated_backpacks/BP/scripts/main.js",import.meta.url),"utf8")
  .replace(/^import .*;$/gm,"").replace(/^export /gm,"");

class Stack {
  constructor(type,amount) {
    this.typeId=type;this.amount=amount;this.nameTag=undefined;this.lore=[];
    this.props={};this.damage=0;this.enchantments=[];
    this.destroy=[];this.place=[];this.keepOnDeath=false;this.lockMode="none";
    this.maxAmount=type==="minizin:backpack"?1:64;
  }
  getDynamicPropertyIds(){return Object.keys(this.props);}
  getDynamicProperty(k){return this.props[k];}
  setDynamicProperty(k,v){this.props[k]=v;}
  getLore(){return this.lore;}setLore(v){this.lore=v;}
  getCanDestroy(){return this.destroy;}getCanPlaceOn(){return this.place;}
  setCanDestroy(v){this.destroy=v;}setCanPlaceOn(v){this.place=v;}
  getComponent(name){
    if(name==="minecraft:durability"){const self=this;return {
      get damage(){return self.damage;},set damage(n){self.damage=n;}
    };}
    if(name==="minecraft:enchantable")return {
      getEnchantments:()=>this.enchantments,addEnchantments:e=>this.enchantments=e
    };
  }
}
function harness() {
  const worldProps=new Map(),playerProps=new Map();
  const signal={subscribe(){}};
  const world={beforeEvents:{playerInteractWithBlock:signal,playerInteractWithEntity:signal},
    afterEvents:{itemUse:signal},
    getDynamicProperty:k=>worldProps.get(k),setDynamicProperty:(k,v)=>worldProps.set(k,v)};
  const inv={size:5,items:[new Stack("minizin:backpack",1)],
    getItem(i){return this.items[i];},setItem(i,item){this.items[i]=item;}};
  const player={id:"P",name:"Player",selectedSlotIndex:0,isValid:true,
    getComponent:()=>({container:inv}),sendMessage(){},
    getDynamicProperty:k=>playerProps.get(k),
    setDynamicProperty:(k,v)=>playerProps.set(k,v)};
  const api=new Function("world","system","ItemStack","EnchantmentTypes",
    "ActionFormData","ModalFormData",source+
    "\nreturn {assign,encode,decode,getState,writeState,migrateLegacy,validate,compatible,depositAll,sortBag};")(
      world,{},Stack,{get:id=>({id})},class {},class {}
    );
  return {api,worldProps,playerProps,inv,player};
}
test("roundtrip preserves item metadata; containers and special items rejected",()=>{
  const {api}=harness(),s=new Stack("minecraft:diamond_sword",1);
  s.nameTag="Unique";s.damage=32;s.props={"custom:x":23};
  s.enchantments=[{type:{id:"sharpness"},level:3}];
  const data=api.encode(s);
  assert.doesNotThrow(()=>api.validate(data));
  assert.deepEqual(api.encode(api.decode(data)),data);
  for(const type of ["minizin:backpack","minecraft:shulker_box",
    "minecraft:filled_map","minecraft:potion"])
    assert.throws(()=>api.encode(new Stack(type,1)));
});
test("each backpack item receives stable identity; v1 data migrates only once",()=>{
  const {api,inv,player,playerProps}=harness();
  const sword=JSON.parse(JSON.stringify(api.encode(new Stack("minecraft:diamond_sword",1))));
  playerProps.set("minizin:personal_backpack_v1",JSON.stringify([sword]));
  const id=api.assign(player);
  assert.equal(api.assign(player),id);
  api.migrateLegacy(player,id);
  assert.deepEqual(api.getState(id).slots[0],sword);
  assert.equal(playerProps.get("minizin:personal_backpack_v1"),undefined);
  const other=new Stack("minizin:backpack",1);
  inv.items[0]=other;
  const second=api.assign(player);
  assert.notEqual(second,id);
  assert.equal(api.getState(second).slots[0],null);
  assert.deepEqual(api.getState(id).slots[0],sword);
});

test("migration never discards legacy data when a target already holds other items",()=>{
  const {api,player,playerProps}=harness();
  const id=api.assign(player);
  const existing=JSON.parse(JSON.stringify(api.encode(new Stack("minecraft:stone",3))));
  api.writeState(id,{slots:[existing,...Array(26).fill(null)],revision:3});
  const old=JSON.parse(JSON.stringify(api.encode(new Stack("minecraft:diamond_sword",1))));
  playerProps.set("minizin:personal_backpack_v1",JSON.stringify([old]));
  assert.throws(()=>api.migrateLegacy(player,id),/Mochila ocupada/);
  assert.deepEqual(JSON.parse(playerProps.get("minizin:personal_backpack_v1")),[old]);
  assert.deepEqual(api.getState(id).slots[0],existing);
});

test("bulk deposit moves real item stacks, keeps individual bag state and sorting",async()=>{
  const {api,inv,player}=harness();
  inv.items[1]=new Stack("minecraft:stone",32);
  inv.items[2]=new Stack("minecraft:diamond_sword",1);
  inv.items[2].nameTag="Named gear";
  const id=api.assign(player);
  await api.depositAll(player,id,0);
  assert.equal(inv.items[1],undefined);
  assert.equal(inv.items[2],undefined);
  const bag=api.getState(id);
  assert.equal(bag.slots[0].amount,32);
  assert.equal(bag.slots[1].name,"Named gear");
  await api.sortBag(player,id,bag.revision);
  assert.equal(api.getState(id).revision,2);
  assert.equal(api.getState(id).slots[0].name,"Named gear");
  assert.equal(api.getState(id).slots[1].amount,32);
});
