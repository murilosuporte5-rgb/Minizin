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
