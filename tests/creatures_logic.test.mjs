import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const code=readFileSync(new URL("../bedrock/packs/creatures/BP/scripts/math.js",import.meta.url),"utf-8");
const {dragonStage,ignisPhase,nearSegment,direction}=await import("data:text/javascript;base64,"+Buffer.from(code).toString("base64"));
test("Ice and Fire dragon five Java day thresholds",()=>{
 for(const [days,expected] of [[0,1],[24,1],[25,2],[49,2],[50,3],[74,3],[75,4],[99,4],[100,5],[150,5]])assert.equal(dragonStage(days),expected);
});
test("Ignis Java phase thresholds",()=>{
 assert.equal(ignisPhase(450,450),0);
 assert.equal(ignisPhase(300,450),1);
 assert.equal(ignisPhase(150,450),2);
 assert.equal(ignisPhase(0,0),0);
});
test("Bluff fissure segment hits the line, not an unbounded area",()=>{
 const a={x:0,z:0},b={x:12,z:0};
 assert.equal(nearSegment({x:5,z:0.5},a,b,1.1),true);
 assert.equal(nearSegment({x:6,z:3},a,b,1.1),false);
 assert.equal(nearSegment({x:14,z:0},a,b,1.1),false);
 assert.deepEqual(direction(a,b),{x:1,z:0});
});
