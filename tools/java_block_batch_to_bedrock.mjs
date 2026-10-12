#!/usr/bin/env node
// Convert Java block-model JSON including inheritance, with clear errors for unsupported cases.
import fs from "node:fs";
import path from "node:path";
import {joinModel,geoFromJava} from "./java_model_to_bedrock.mjs";
let root,ns,out;
const a=process.argv.slice(2);
for(let i=0;i<a.length;i++){
 if(a[i]==="--root")root=a[++i];
 else if(a[i]==="--namespace")ns=a[++i];
 else if(a[i]==="--output")out=a[++i];
 else throw Error("unknown argument "+a[i]);
}
if(!root||!ns||!out)throw Error("Missing --root --namespace --output");
const bases=["common/src/main/resources","common/src/generated/resources","src/main/resources","src/generated/resources"];
function baseFile(namespace,what,extension){
 return bases.map(b=>path.join(root,b,"assets",namespace,what+extension)).find(fs.existsSync);
}
function vanilla(parent){
 if(!["block/cube_all","minecraft:block/cube_all"].includes(parent))return null;
 return {elements:[{from:[0,0,0],to:[16,16,16],faces:Object.fromEntries(
 ["north","south","east","west","up","down"].map(f=>[f,{uv:[0,0,16,16],texture:"#all"}]))}],textures:{all:"#all"}};
}
function resolve(loc,visiting=[]){
 if(visiting.includes(loc))throw Error("model cyclic parent "+loc);
 const seg=loc.includes(":")?loc.split(":",2):[ns,loc];
 const file=baseFile(seg[0],"models/"+seg[1],".json");
 if(!file)throw Error("missing parent "+loc);
 const current=JSON.parse(fs.readFileSync(file,"utf8"));
 if(!current.parent)return current;
 return joinModel(vanilla(current.parent)||resolve(current.parent,[...visiting,loc]),current);
}
function texInfo(id){
 if(!id)return [16,16];
 const [namespace,name]=id.includes(":")?id.split(":",2):[ns,id];
 const f=baseFile(namespace,"textures/"+name,".png");
 if(!f)return [16,16];
 const bytes=fs.readFileSync(f);
 if(bytes.length>24&&bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))
 return [bytes.readUInt32BE(16),bytes.readUInt32BE(20)];
 return [16,16];
}
const all=new Map();
for(const base of bases){
 const folder=path.join(root,base,"assets",ns,"models/block");
 if(fs.existsSync(folder))for(const ent of fs.readdirSync(folder,{withFileTypes:true})){
  if(ent.isFile()&&ent.name.endsWith(".json"))all.set(ent.name.slice(0,-5),"block/"+ent.name.slice(0,-5));
 }
}
fs.mkdirSync(out,{recursive:true});
const rows=[];
for(const name of [...all.keys()].sort()){
 if(name.endsWith("_top")&&all.has(name.slice(0,-4)+"_bottom"))continue;
 const maybeTop=name.endsWith("_bottom")?name.slice(0,-7)+"_top":null;
 const paired=maybeTop&&all.has(maybeTop);
 const names=paired?[all.get(name),all.get(maybeTop)]:[all.get(name)];
 const entry={name,models:names,status:"failed"};
 try{
  const parts=names.map((loc,i)=>({model:resolve(loc),yOffset:16*i}));
  const declared=parts.flatMap(p=>Object.values(p.model.textures||{})).filter(s=>typeof s==="string"&&!s.startsWith("#"));
  const [w,h]=texInfo(declared[0]);
  const geometryId="geometry.minizin."+ns+"."+name.replace(/[^A-Za-z0-9_]/g,"_").toLowerCase();
  const result=geoFromJava(parts,{width:w,height:h,identifier:geometryId});
  if(!result.texture)throw Error("source texture unresolved");
  const file=path.join(out,name+".geo.json");
  fs.writeFileSync(file,JSON.stringify(result.geometry,null,2)+"\n","utf8");
  entry.status="converted";entry.texture=result.texture;entry.atlas=[w,h];
  entry.cubes=parts.reduce((n,p)=>n+p.model.elements.length,0);
 }catch(e){entry.error=String(e.message||e);}
 rows.push(entry);
}
const converted=rows.filter(x=>x.status==="converted").length;
const index={namespace:ns,total:rows.length,converted,failed:rows.length-converted,results:rows};
fs.writeFileSync(path.join(out,"conversion_index.json"),JSON.stringify(index,null,2)+"\n");
console.log(JSON.stringify({namespace:ns,total:index.total,converted,failed:index.failed,
 failures:rows.filter(x=>x.status==="failed").slice(0,5)},null,2));
if(converted===0)process.exitCode=2;
