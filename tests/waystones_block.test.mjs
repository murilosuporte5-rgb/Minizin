import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";

const src=readFileSync(new URL("../bedrock/runtime/waystones_block.js",import.meta.url),"utf8")
  .replace(/^import .*;$/gm,"").replace(/^export /gm,"");
function harness(){
  const worldProps=new Map(),playerProps=new Map(),blocks=new Map();
  const at=loc=>[loc.x,loc.y,loc.z].join(",");
  let component,interval;
  const dimension={id:"minecraft:overworld",getBlock:loc=>blocks.get(at(loc)),
    getEntities(){return this.entities||[];}};
  const makeBlock=(x,y,z,typeId)=>{
    const location={x,y,z};
    return {location,dimension,typeId,isAir:typeId==="minecraft:air",isLiquid:false,
      permutation:{withState(){return this;}},setPermutation(){},
      setType(type){this.typeId=type;this.isAir=type==="minecraft:air";}};
  };
  const player={id:"Player",name:"Tester",isValid:true,
    location:{x:1,y:65,z:1},dimension,sendMessage(){},teleport(){},
    getDynamicProperty:k=>playerProps.get(k),
    setDynamicProperty:(k,v)=>playerProps.set(k,v)};
  const signal={subscribe(){}};
  const world={afterEvents:{playerBreakBlock:signal,playerLeave:signal},
    getDimension:()=>dimension,getAllPlayers:()=>[player],
    getDynamicProperty:k=>worldProps.get(k),
    setDynamicProperty:(k,v)=>worldProps.set(k,v)};
  const system={currentTick:100,
    beforeEvents:{startup:{subscribe:fn=>fn({blockComponentRegistry:{
      registerCustomComponent:(id,api)=>component={id,api}
    }})}},run:fn=>fn(),runInterval:fn=>interval=fn};
  const api=new Function("world","system","ActionFormData","ModalFormData",
    src+"\nreturn {register,migrate,travelTo,deleteRecord};"
  )(world,system,class {},class {});
  return {api,component,interval,worldProps,playerProps,blocks,at,makeBlock,player,dimension};
}
test("block is registered via v2 custom component, without entity interaction",()=>{
  const h=harness();
  assert.equal(h.component.id,"minizin:waystone_control");
  const block=h.makeBlock(1,64,1,"minizin:andesite_waystone_block");
  h.blocks.set(h.at(block.location),block);
  h.component.api.onPlace({block});
  const rows=JSON.parse(h.worldProps.get("minizin:waystones_world_v1"));
  assert.equal(rows.length,1);
  assert.ok(rows[0].id.startsWith("ws_"));
});
test("legacy marker migrates without replacing occupied blocks or losing known IDs",()=>{
  const h=harness(),marker={id:"old_entity",location:{x:10.5,y:64,z:10.5},
    dimension:h.dimension,getDynamicProperty:()=> "ws_preexisting",
    remove(){this.removed=true;}};
  const location={x:10,y:64,z:10};
  const air=h.makeBlock(10,64,10,"minecraft:air");
  h.blocks.set(h.at(location),air);
  h.worldProps.set("minizin:waystones_world_v1",JSON.stringify([{
    id:"ws_preexisting",name:"Minha Casa",dimension:"overworld",
    x:10.5,y:64,z:10.5
  }]));
  h.playerProps.set("minizin:waystones_known_v1",JSON.stringify(["ws_preexisting"]));
  h.dimension.entities=[marker];
  h.interval();
  assert.equal(air.typeId,"minizin:andesite_waystone_block");
  assert.equal(marker.removed,true);
  const rows=JSON.parse(h.worldProps.get("minizin:waystones_world_v1"));
  assert.equal(rows.length,1);
  assert.equal(rows[0].name,"Minha Casa");
  assert.equal(rows[0].id,"ws_preexisting");
  assert.deepEqual(JSON.parse(h.playerProps.get("minizin:waystones_known_v1")),["ws_preexisting"]);
});
