import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const script=readFileSync(new URL('../bedrock/runtime/item_actions.js',import.meta.url),'utf8').replace(/^import .*;\n/gm,'');
function harness(affinity=50){
  const callbacks={},messages=[];let origins=0;
  const event=key=>({subscribe:fn=>(callbacks[key]??=[]).push(fn)});
  const world={beforeEvents:{playerInteractWithEntity:event('entity'),playerInteractWithBlock:event('block')},
    afterEvents:{itemUse:event('use')}};
  const player={id:'p1',isValid:true,dimension:{id:'overworld'},location:{x:0,y:0,z:0},selectedSlotIndex:0,data:{}};
  const npc={id:'npc',typeId:'minizin:mca_female_0',isValid:true,dimension:{id:'overworld'},location:{x:1,y:0,z:0},
    data:{'minizin:mca_relationship_v1_players':{p1:{value:affinity}}}};
  let held={typeId:'minizin:mca_item_engagement_ring',amount:1};
  const inv={getItem:()=>held,setItem:(_,value)=>held=value};
  new Function('world','system','chooseOrigin','container','read','write','tell',script)(world,{run:fn=>fn()},
    ()=>origins++,()=>inv,(entity,key,fallback)=>entity.data[key]??fallback,
    (entity,key,value)=>entity.data[key]=value,(_,message)=>messages.push(message));
  return {player,npc,messages,get held(){return held;},get origins(){return origins;},
    offer(){const ev={player,target:npc,itemStack:held,cancel:false};for(const fn of callbacks.entity)fn(ev);return ev;},
    orb(){for(const fn of callbacks.block)fn({player,itemStack:{typeId:'minizin:origins_item_orb_of_origin'},isFirstEvent:true});}};
}
test('insufficient affinity preserves the ring and does not bind either side',()=>{
  const h=harness(49);h.offer();assert.equal(h.held.amount,1);assert.equal(h.npc.data['minizin:mca_pair_v1'],undefined);
});
test('engagement persists both partners and consumes exactly one held ring',()=>{
  const h=harness(50);assert.equal(h.offer().cancel,true);assert.equal(h.held,undefined);
  assert.deepEqual(h.npc.data['minizin:mca_pair_v1'],{partner:'p1',stage:'engaged'});
  assert.deepEqual(h.player.data['minizin:mca_pair_v1'],{partner:'npc',stage:'engaged'});
});
test('another partner cannot overwrite relationship or lose their ring',()=>{
  const h=harness(100);h.npc.data['minizin:mca_pair_v1']={partner:'p2',stage:'married'};
  h.offer();assert.equal(h.held.amount,1);assert.equal(h.npc.data['minizin:mca_pair_v1'].partner,'p2');
});
test('original Origins orb opens selection on block interaction',()=>{
  const h=harness();h.orb();assert.equal(h.origins,1);
});
