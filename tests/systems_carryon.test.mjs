import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const source=readFileSync(new URL("../bedrock/packs/next_four/BP/scripts/carryon.js",import.meta.url),"utf8")
  .replace(/^import .*;$/gm,"").replace(/^export /gm,"");
test("chest is moved using persisted structure and not cloned",()=>{
  const records=new Map(),props=new Map(),blocks=new Map();
  const k=p=>p.x+","+p.y+","+p.z;
  let unloadOrigin=false;
  const dimension={id:"minecraft:overworld",getBlock(pos){
    if(unloadOrigin&&k(pos)==="1,64,0")return undefined;
    if(!blocks.has(k(pos))){
      const block={location:{...pos},typeId:"minecraft:air",isAir:true,dimension,
        data:[],setType(type){this.typeId=type;this.isAir=type==="minecraft:air";}};
      blocks.set(k(pos),block);
    }
    return blocks.get(k(pos));
  }};
  const src=dimension.getBlock({x:1,y:64,z:0});
  src.setType("minecraft:chest");src.data=["diamond","book"];
  const structures=new Map();
  const manager={
    createFromWorld(id,dim,a,b){structures.set(id,{type:dim.getBlock(a).typeId,data:[...dim.getBlock(a).data]});},
    get:id=>structures.get(id),
    place(id,dim,p){const record=structures.get(id),dest=dim.getBlock(p);
      dest.setType(record.type);dest.data=[...record.data];},
    delete:id=>structures.delete(id)
  };
  const signal={subscribe(){}},world={structureManager:manager,
    beforeEvents:{playerInteractWithBlock:signal},
    afterEvents:{playerInteractWithEntity:signal,playerSpawn:signal,playerLeave:signal},
    getDimension:()=>dimension};
  const system={run:fn=>fn(),runTimeout:fn=>fn(),runInterval(){}};
  const player={id:"user1",name:"Tester",dimension,location:{x:1,y:64,z:1},isValid:true,
    getDynamicProperty:id=>props.get(id),setDynamicProperty:(id,v)=>props.set(id,v)};
  const notices=[];
  const api=new Function("world","system","held","tell",source+
    "\nreturn {grab,put,pickedBlock,recoverBlock};")(world,system,()=>null,(p,t)=>notices.push(t));
  api.grab(player,src.location,dimension.id);
  assert.equal(src.typeId,"minecraft:air");
  assert.equal(api.pickedBlock(player),"minecraft:chest");
  assert.equal(structures.size,1);
  const support=dimension.getBlock({x:2,y:64,z:0});
  support.setType("minecraft:stone");
  unloadOrigin=true;
  api.put(player,support.location,"Up");
  assert.equal(api.pickedBlock(player),"minecraft:chest");
  assert.equal(api.recoverBlock(player),true); // still held, no second structure placed
  unloadOrigin=false;
  api.put(player,support.location,"Up");
  const dest=dimension.getBlock({x:2,y:65,z:0});
  assert.equal(dest.typeId,"minecraft:chest");
  assert.deepEqual(dest.data,["diamond","book"]);
  assert.equal(api.pickedBlock(player),null);
  assert.equal(structures.size,0);
});

test("Carry On follows Java blacklist boundaries while accepting ordinary vanilla blocks",()=>{
  const api=new Function(source+"\nreturn {isCarryableBlock,isCarryableEntity};")();
  assert.equal(api.isCarryableBlock({typeId:"minecraft:barrel",isAir:false}),true);
  assert.equal(api.isCarryableBlock({typeId:"minecraft:glass",isAir:false}),true);
  assert.equal(api.isCarryableBlock({typeId:"minecraft:oak_door",isAir:false}),false);
  assert.equal(api.isCarryableBlock({typeId:"minecraft:end_portal",isAir:false}),false);
  assert.equal(api.isCarryableEntity({typeId:"minecraft:cat",isValid:true}),true);
  assert.equal(api.isCarryableEntity({typeId:"minecraft:ender_dragon",isValid:true}),false);
  assert.equal(api.isCarryableEntity({typeId:"minizin_cataclysm:ignis",getComponent(){return {};}}),true);
});
