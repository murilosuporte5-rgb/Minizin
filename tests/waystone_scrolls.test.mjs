import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../bedrock/runtime/waystone_scrolls.js',import.meta.url),'utf8')
  .replace(/^import .*;$/gm,'').replace(/^export /gm,'');

class FakeItem {
  constructor(typeId,amount=1){this.typeId=typeId;this.amount=amount;this.props={};}
  setDynamicProperty(k,v){this.props[k]=v;}
  getDynamicProperty(k){return this.props[k];}
}
class FakeItemStack extends FakeItem {}
function harness(){
  const callbacks={},messages=[],worldProps=new Map(),playerProps=new Map();
  const signal=name=>({subscribe:fn=>(callbacks[name]??=[]).push(fn)});
  let held=new FakeItem('minizin:blank_scroll',1),travel=[];
  const inv={getItem:()=>held,setItem:(_,value)=>{held=value;},addItem:item=>item};
  const dimension={id:'minecraft:overworld',spawnItem(){}};
  const player={id:'p1',isValid:true,name:'Tester',selectedSlotIndex:0,location:{x:0,y:64,z:0},dimension,
    getGameMode:()=> 'survival',getComponent:id=>id==='minecraft:inventory'?{container:inv}:undefined,
    getDynamicProperty:k=>playerProps.get(k),setDynamicProperty:(k,v)=>playerProps.set(k,v),sendMessage:m=>messages.push(m)};
  const block={typeId:'minizin:andesite_waystone_block',location:{x:4,y:64,z:4},dimension};
  const world={beforeEvents:{playerInteractWithBlock:signal('block')},afterEvents:{itemUse:signal('use'),playerLeave:signal('leave')},
    getDynamicProperty:k=>worldProps.get(k),setDynamicProperty:(k,v)=>worldProps.set(k,v)};
  const system={currentTick:100,run:fn=>fn()};
  const ActionFormData=class{};
  const travelTo=(p,id,options)=>{travel.push({p,id,options});options.onComplete(true);return true;};
  new Function('world','system','ItemStack','ActionFormData','travelTo',source)(world,system,FakeItemStack,ActionFormData,travelTo);
  return {callbacks,worldProps,playerProps,player,block,messages,get held(){return held;},set held(v){held=v;},travel,signal};
}

test('blank scroll binds to the real registered waystone and preserves the source icon item',()=>{
  const h=harness();
  h.worldProps.set('minizin:waystones_world_v1',JSON.stringify([{id:'ws_home',name:'Casa',dimension:'minecraft:overworld',x:4,y:64,z:4}]));
  const event={player:h.player,block:h.block,itemStack:h.held,isFirstEvent:true,cancel:false};
  h.callbacks.block[0](event);
  assert.equal(event.cancel,true);
  assert.equal(h.held.typeId,'minizin:bound_scroll');
  assert.equal(h.held.getDynamicProperty('minizin:waystone_id'),'ws_home');
  assert.equal(h.held.nameTag,'Casa');
  assert.match(h.messages.at(-1),/Casa/);
});

test('bound scroll invokes safe travel without requiring a second manual activation and consumes on success',()=>{
  const h=harness();
  h.held=new FakeItem('minizin:bound_scroll',1);h.held.setDynamicProperty('minizin:waystone_id','ws_home');
  const event={source:h.player,itemStack:h.held};
  h.callbacks.use[0](event);
  assert.equal(h.travel.length,1);
  assert.equal(h.travel[0].id,'ws_home');
  assert.equal(h.travel[0].options.requireKnown,false);
  assert.equal(h.held,undefined);
});

test('standalone Waystones uses the same completion-capable travel runtime as the combined pack',()=>{
  const runtime=readFileSync(new URL('../bedrock/runtime/waystones_block.js',import.meta.url),'utf8');
  const standalone=readFileSync(new URL('../bedrock/packs/waystones/BP/scripts/waystones_block.js',import.meta.url),'utf8');
  assert.equal(standalone,runtime);
  assert.match(standalone,/onComplete/);
  assert.match(standalone,/requireKnown/);
});
