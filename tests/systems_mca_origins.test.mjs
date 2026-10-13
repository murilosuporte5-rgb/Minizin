import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";

const scripts="../bedrock/packs/next_four/BP/scripts/";
const load=(name)=>readFileSync(new URL(scripts+name+".js",import.meta.url),"utf8")
  .replace(/^import .*;$/gm,"").replace(/^export /gm,"");
const hook={subscribe(){}};
class Form {
  static selection=0;
  title(){return this;}
  body(){return this;}
  button(){return this;}
  async show(){return {canceled:false,selection:Form.selection};}
}
const get=(o,k)=>o.properties.get(k);
const set=(o,k,v)=>o.properties.set(k,v);
function holder() {
  return {isValid:true,properties:new Map(),
    getDynamicProperty(k){return get(this,k);},
    setDynamicProperty(k,v){set(this,k,v);}};
}
const read=(o,k,fallback)=>{try{return JSON.parse(get(o,k))??fallback;}catch{return fallback;}};
const write=(o,k,data)=>set(o,k,JSON.stringify(data));
test("MCA records player-specific marriage, child birth and fidelity to identity",async()=>{
  const spawned=[];
  const dim={id:"minecraft:overworld",
    getBlock:()=>({isAir:true}),
    spawnEntity(id,loc,opts) {
      const baby={...holder(),typeId:id,location:loc,getComponent:name=>
        name==="minecraft:ageable"?{duration:24000}:undefined};
      spawned.push({id,loc,opts,baby});return baby;
    }};
  const player={...holder(),id:"player1",location:{x:0,y:64,z:0},dimension:dim};
  const npc={...holder(),id:"npc1",nameTag:"Alex",location:{x:1,y:64,z:0},dimension:dim};
  set(player,"minizin:mca_person_v2","mca_player_10000");
  set(npc,"minizin:mca_person_v2","mca_npc_20000");
  write(npc,"minizin:mca_relation_v2",{mca_player_10000:{affinity:95,last:0,married:false,children:0}});
  const world={getAbsoluteTime:()=>50000,afterEvents:{playerInteractWithEntity:hook,playerLeave:hook}};
  const engine=new Function("world","system","ActionFormData","tell","hasItem","takeOne","clamp","read","write","held",
    load("mca")+"\nreturn {show};"
  )(world,{run:f=>f()},Form,()=>{},()=>true,()=>true,(n,l,h)=>Math.max(l,Math.min(h,n)),read,write,()=>undefined);
  Form.selection=3;
  await engine.show(player,npc);
  assert.equal(get(player,"minizin:mca_spouse_v2"),"mca_npc_20000");
  assert.equal(get(npc,"minizin:mca_spouse_v2"),"mca_player_10000");
  assert.equal(read(npc,"minizin:mca_relation_v2",{}).mca_player_10000.married,true);
  Form.selection=4;
  await engine.show(player,npc);
  assert.equal(spawned.length,1);
  assert.equal(spawned[0].opts.spawnEvent,"minecraft:entity_born");
  assert.deepEqual(read(spawned[0].baby,"minizin:mca_family_v2",{}),{
    player:"mca_player_10000",npc:"mca_npc_20000"
  });
  assert.equal(read(npc,"minizin:mca_relation_v2",{}).mca_player_10000.children,1);
});

test("MCA profession selection persists the Java profession identity",async()=>{
  const dim={id:"minecraft:overworld",getBlock:()=>({isAir:true})};
  const player={...holder(),id:"profession-player",location:{x:0,y:64,z:0},dimension:dim};
  const npc={...holder(),id:"profession-npc",location:{x:1,y:64,z:0},dimension:dim};
  const world={getAbsoluteTime:()=>50000,afterEvents:{playerInteractWithEntity:hook,playerLeave:hook}};
  const engine=new Function("world","system","ActionFormData","tell","hasItem","takeOne","clamp","read","write","held",
    load("mca")+"\nreturn {chooseProfession};"
  )(world,{run:f=>f()},Form,()=>{},()=>false,()=>false,(n,l,h)=>Math.max(l,Math.min(h,n)),read,write,()=>undefined);
  Form.selection=1;
  await engine.chooseProfession(player,npc);
  assert.equal(get(npc,"minizin:mca_profession_v2"),"guard");
});

test("Origins stores active cooldown and avoids repeat Elytrian impulses",()=>{
  const source=load("origins");
  const world={getAllPlayers:()=>[],afterEvents:{playerLeave:hook,itemUse:hook,playerInteractWithBlock:hook}};
  const system={currentTick:1000,runInterval(){},run(f){f();}};
  const player={...holder(),id:"pilot",impulses:[],
    applyImpulse(vec){this.impulses.push(vec);}};
  set(player,"minizin:origin_v1","elytrian");
  const catalog=[{id:"elytrian",label:"Elytrian"}],implemented={};
  const m=new Function("world","system","ActionFormData","ORIGINS_CATALOG","IMPLEMENTED_PASSIVES","tell",
    source+"\nreturn {activateOrigin};")(world,system,Form,catalog,implemented,()=>{});
  m.activateOrigin(player);
  m.activateOrigin(player);
  assert.equal(player.impulses.length,1);
  assert.deepEqual(player.impulses[0],{x:0,y:1.2,z:0});
  system.currentTick+=200;
  m.activateOrigin(player);
  assert.equal(player.impulses.length,2);
});

test("Origins applies real fire immunity, water vulnerability and passive movement mappings",()=>{
  const source=load("origins");
  const callbacks={hurt:[],hit:[],leave:[],use:[],block:[]};
  const signal=name=>({subscribe(fn){callbacks[name].push(fn);}});
  const world={getAllPlayers:()=>[],
    beforeEvents:{entityHurt:signal("hurt")},
    afterEvents:{playerLeave:signal("leave"),entityHitEntity:signal("hit"),itemUse:signal("use"),playerInteractWithBlock:signal("block")}};
  const system={currentTick:1000,interval:null,runInterval(fn){this.interval=fn;},run(fn){fn();}};
  const effects=[];
  const player={...holder(),id:"origin-player",typeId:"minecraft:player",isOnFire:true,isOnGround:false,
    isSprinting:true,isSneaking:false,isInWater:false,location:{x:0,y:64,z:0},dimension:{getBlock:()=>({isAir:true})},
    addEffect(...args){effects.push(args);},applyDamage(){this.damage=(this.damage??0)+1;}};
  world.getAllPlayers=()=>[player];
  set(player,"minizin:origin_v1","blazeborn");
  const m=new Function("world","system","ActionFormData","ORIGINS_CATALOG","IMPLEMENTED_PASSIVES","tell",
    source+"\nreturn {installOrigins};")(world,system,Form,[],{},()=>{});
  m.installOrigins();
  const fire={hurtEntity:player,damageSource:{cause:"fire"},cancel:false};
  callbacks.hurt[0](fire);
  assert.equal(fire.cancel,true);
  set(player,"minizin:origin_v1","feline");
  player.isOnFire=false;
  const fall={hurtEntity:player,damageSource:{cause:"fall"},cancel:false};
  callbacks.hurt[0](fall);
  assert.equal(fall.cancel,true);
  set(player,"minizin:origin_v1","merling");
  player.isInWater=true;
  system.interval();
  assert.ok(effects.some(([name])=>name==="water_breathing"));
  // The event adapter is also exercised directly so the Java burning-wrath
  // damage is not represented only by a decorative status message.
  set(player,"minizin:origin_v1","blazeborn");
  player.isOnFire=true;
  let extra=0;
  callbacks.hit[0]({damagingEntity:player,hitEntity:{isValid:true,applyDamage(n){extra+=n;}}});
  assert.equal(extra,3);
  assert.equal(typeof callbacks.hit[0],"function");
});

test("Origins Enderian launches a real Bedrock Ender Pearl with the Java cooldown",()=>{
  const source=load("origins");
  const pearls=[];
  const player={...holder(),id:"ender-player",location:{x:0,y:64,z:0},
    getViewDirection(){return {x:0,y:0,z:1};},
    getHeadLocation(){return {x:0,y:65.5,z:0};},
    dimension:{spawnEntity(type,location){const pearl={type,location,impulses:[],applyImpulse(v){this.impulses.push(v);}};pearls.push(pearl);return pearl;}}};
  set(player,"minizin:origin_v1","enderian");
  const system={currentTick:1000};
  const m=new Function("world","system","ActionFormData","ORIGINS_CATALOG","IMPLEMENTED_PASSIVES","tell",
    source+"\nreturn {activateOrigin};")({afterEvents:{}},system,Form,[],{},()=>{});
  m.activateOrigin(player);
  m.activateOrigin(player);
  assert.equal(pearls.length,1);
  assert.equal(pearls[0].type,"minecraft:ender_pearl");
  assert.deepEqual(pearls[0].impulses[0],{x:0,y:0,z:1.5});
  system.currentTick+=30;
  m.activateOrigin(player);
  assert.equal(pearls.length,2);
});

test("Origins Shulk inventory persists a real item payload across UI transfers",async()=>{
  const source=load("origins");
  class Stack{
    constructor(type,amount){this.typeId=type;this.amount=amount;this.nameTag=undefined;this.lore=[];this.props={};this.damage=0;}
    getDynamicPropertyIds(){return Object.keys(this.props);}
    getDynamicProperty(k){return this.props[k];}
    setDynamicProperty(k,v){this.props[k]=v;}
    getLore(){return this.lore;}
    setLore(v){this.lore=v;}
    getCanDestroy(){return ["minecraft:stone"];}
    getCanPlaceOn(){return ["minecraft:dirt"];}
    getComponent(name){
      if(name==="minecraft:durability")return {damage:this.damage};
      if(name==="minecraft:enchantable")return {getEnchantments:()=>[{type:{id:"minecraft:sharpness"},level:2}],addEnchantments(){}};
      return undefined;
    }
  }
  const callbacks={};const signal=name=>({subscribe(fn){callbacks[name]=fn;}});
  const world={getAllPlayers:()=>[],beforeEvents:{entityHurt:signal("hurt"),chatSend:signal("chat")},
    afterEvents:{playerLeave:signal("leave"),entityHitEntity:signal("hit"),itemUse:signal("use"),playerInteractWithBlock:signal("block")}};
  const system={currentTick:1000,runInterval(){},run(fn){fn();}};
  const messages=[];
  const slot=new Stack("minecraft:diamond_pickaxe",2);slot.nameTag="Picareta fiel";slot.lore=["Java"];
  slot.props["minizin:test"]="preservar";slot.damage=7;
  const items=[slot];const container={getItem(i){return items[i];},setItem(i,v){items[i]=v;}};
  const player={...holder(),id:"shulk-player",isValid:true,selectedSlotIndex:0,
    getComponent(name){return name==="minecraft:inventory"?{container}:undefined;},sendMessage(m){messages.push(m);}};
  set(player,"minizin:origin_v1","shulk");
  const engine=new Function("world","system","ActionFormData","ORIGINS_CATALOG","IMPLEMENTED_PASSIVES","tell","ItemStack","EnchantmentTypes",
    source+"\nreturn {openShulkInventory};")(world,system,Form,[],{},(p,m)=>messages.push(m),Stack,{get:()=>({id:"minecraft:sharpness"})});
  Form.selection=0;
  await engine.openShulkInventory(player);
  assert.equal(items[0],undefined);
  const saved=JSON.parse(get(player,"minizin:origins_shulk_inventory_v1"));
  assert.equal(saved[0].type,"minecraft:diamond_pickaxe");
  assert.equal(saved[0].name,"Picareta fiel");
  assert.equal(saved[0].amount,2);
  assert.equal(saved[0].props["minizin:test"],"preservar");
  await engine.openShulkInventory(player);
  assert.equal(items[0].typeId,"minecraft:diamond_pickaxe");
  assert.equal(items[0].amount,2);
  assert.equal(items[0].nameTag,"Picareta fiel");
});
