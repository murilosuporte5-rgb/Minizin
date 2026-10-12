import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../bedrock/runtime/aether_equipment.js',import.meta.url),'utf8').replace(/^import .*;\n/gm,'');
function harness(power){
  const callbacks={};const signal=name=>({subscribe:fn=>callbacks[name]=fn});
  const world={afterEvents:{entityHitEntity:signal('hit'),playerBreakBlock:signal('break'),playerLeave:signal('leave')},
    beforeEvents:{playerInteractWithBlock:signal('interact')},getAllPlayers:()=>[]};
  const system={currentTick:100,runInterval(){},run:fn=>fn()};
  const durability={damage:0,maxDurability:502};let held={typeId:'test:sword',getComponent:id=>id==='minecraft:durability'?durability:
      id==='minecraft:enchantable'?{getEnchantment:()=>({level:2})}:undefined};
  const inv={getItem:()=>held,setItem:(_,item)=>held=item},health={currentValue:19.5,effectiveMax:20,setCurrentValue:v=>health.currentValue=v};
  const p={id:'p1',typeId:'minecraft:player',selectedSlotIndex:0,getComponent:id=>id==='minecraft:inventory'?{container:inv}:health};
  const target={fire:0,setOnFire:n=>target.fire=n};
  new Function('world','system','EquipmentSlot','EntityDamageCause','EQUIPMENT',source)(world,system,{}, {}, {'test:sword':{power}});
  return {p,target,durability,health,system,get held(){return held;},hit:()=>callbacks.hit({damagingEntity:p,hitEntity:target})};
}
test('flaming sword retains original 30 seconds plus fire-aspect extension',()=>{const h=harness('flaming');h.hit();assert.equal(h.target.fire,38);assert.equal(h.durability.damage,1);});
test('vampire blade heals one point without exceeding max health',()=>{const h=harness('vampire');h.hit();assert.equal(h.health.currentValue,20);});
test('weapon breaks without setting damage past maximum',()=>{const h=harness('flaming');h.durability.damage=501;h.hit();assert.equal(h.held,undefined);assert.equal(h.durability.damage,501);});
test('ability cooldown prevents repeated healing from rapid attacks',()=>{const h=harness('vampire');h.health.currentValue=10;h.hit();h.hit();assert.equal(h.health.currentValue,11);h.system.currentTick+=12;h.hit();assert.equal(h.health.currentValue,12);});
