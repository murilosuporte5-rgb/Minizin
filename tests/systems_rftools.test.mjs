import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const source=readFileSync(new URL("../bedrock/packs/next_four/BP/scripts/rftools.js",import.meta.url),"utf8")
  .replace(/^import .*;$/gm,"").replace(/^export /gm,"");
test("power crosses a cable, enters a cell and lights an actual lamp state",()=>{
  const props=new Map(),blocks=new Map(),p=x=>x.x+","+x.y+","+x.z;
  const signal={subscribe(){}},dimension={id:"minecraft:overworld",getBlock:pos=>blocks.get(p(pos))};
  function make(type,x){
    const block={typeId:type,location:{x,y:64,z:0},dimension,
      permutation:{getState(){return false;},withState(_,lit){return {
        getState(){return lit;},withState:this.withState};}},
      setPermutation(next){this.permutation=next;}};
    blocks.set(p(block.location),block);return block;
  }
  const gen=make("minizin:rftools_generator",0);
  make("minizin:rftools_cable",1);
  const cell=make("minizin:rftools_cell",2);
  const lamp=make("minizin:rftools_lamp",3);
  const world={afterEvents:{playerInteractWithBlock:signal,playerPlaceBlock:signal,
    playerBreakBlock:signal},getDimension:()=>dimension,
    getDynamicProperty:k=>props.get(k),setDynamicProperty:(k,v)=>props.set(k,v)};
  let tick;
  const system={runInterval:fn=>tick=fn,run:fn=>fn()};
  const read=(holder,key,otherwise)=>{try{return JSON.parse(holder.getDynamicProperty(key))??otherwise;}catch{return otherwise;}};
  const write=(holder,key,val)=>holder.setDynamicProperty(key,JSON.stringify(val));
  const fn=new Function("world","system","ActionFormData","tell","hasItem","takeOne","clamp","read","write",
    source+"\nreturn {tick,linked,register};");
  const api=fn(world,system,class {},()=>{},()=>false,()=>false,(n,l,h)=>Math.max(l,Math.min(h,n)),read,write);
  const key=x=>"minecraft:overworld:"+x+",64,0";
  props.set("minizin:rftools_grid_v2",JSON.stringify({
    [key(0)]:{type:gen.typeId,energy:80},
    [key(2)]:{type:cell.typeId,energy:0},
    [key(3)]:{type:lamp.typeId,energy:0}
  }));
  tick();
  const db=read(world,"minizin:rftools_grid_v2",{});
  assert.equal(db[key(0)].energy,40);
  assert.equal(db[key(2)].energy,38);
  assert.equal(lamp.permutation.getState("minizin:lit"),true);
  assert.equal(api.linked(gen).some(x=>x.id===key(2)),true);
});

test("RFTools machine runtime migrates v2 state and transfers into advanced cells",()=>{
  const source=readFileSync(new URL("../bedrock/runtime/rftools_machines.js",import.meta.url),"utf8")
    .replace(/^import .*;$/gm,"");
  const props=new Map(),blocks=new Map(),p=x=>x.x+","+x.y+","+x.z;
  const signal={subscribe(){}};
  const dimension={id:"minecraft:overworld",getBlock:pos=>blocks.get(p(pos))};
  const make=(type,x)=>{const b={typeId:type,location:{x,y:64,z:0},dimension};blocks.set(p(b.location),b);return b;};
  const gen=make("minizin_rftools:coalgenerator",0),cell=make("minizin_rftools:powercell_advanced",1);
  const world={afterEvents:{playerInteractWithBlock:signal,playerBreakBlock:signal},getDimension:()=>dimension,
    getDynamicProperty:k=>props.get(k),setDynamicProperty:(k,v)=>props.set(k,v)};
  const system={interval:null,runInterval(fn){this.interval=fn;},run(fn){fn();}};
  const read=(holder,key,fallback)=>{try{return JSON.parse(holder.getDynamicProperty(key))??fallback;}catch{return fallback;}};
  const write=(holder,key,value)=>holder.setDynamicProperty(key,JSON.stringify(value));
  new Function("world","system","ActionFormData","ItemStack","read","write","takeOne","tell","container",
    source+"\nreturn {};"
  )(world,system,class {},class {},read,write,()=>false,()=>{},()=>undefined);
  const key=x=>"minecraft:overworld:"+x+",64,0";
  props.set("minizin:rftools_machines_v2",JSON.stringify({
    [key(0)]:{type:gen.typeId,energy:100,dimension:dimension.id,location:gen.location},
    [key(1)]:{type:cell.typeId,energy:3995,dimension:dimension.id,location:cell.location}
  }));
  system.interval();
  const migrated=read(world,"minizin:rftools_machines_v3",{});
  assert.equal(migrated[key(0)].energy,95);
  assert.equal(migrated[key(1)].energy,4000);
});
