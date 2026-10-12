import fs from "node:fs";import path from "node:path";
export function joinModel(parent, child){return {...parent,...child,textures:{...parent.textures,...child.textures},elements:child.elements??parent.elements};}
export function geoFromJava(parts,opts={}){
 const w=opts.width||16,h=opts.height||16,textureIds=new Set(),bones=[];
 for(let i=0;i<parts.length;i++){
  const {model,yOffset=0}=parts[i],cubes=[],textures=model.textures||{};
  for(const el of model.elements||[]){
   if(!Array.isArray(el.from)||!Array.isArray(el.to)||el.from.length!==3||el.to.length!==3)throw Error("invalid element");
   const uv={};
   for(const [face,def] of Object.entries(el.faces||{})){
    let t=def.texture||"#texture",limit=0;
    while(t?.startsWith("#")&&++limit<16)t=textures[t.slice(1)];
    if(!t||t.startsWith("#"))throw Error("texture unresolved");
    textureIds.add(t);
    if(!Array.isArray(def.uv)||def.uv.length!==4||def.rotation)throw Error("requires explicit UV without face rotation");
    const [u,v,ue,ve]=def.uv;uv[face]={uv:[u*w/16,v*h/16],uv_size:[(ue-u)*w/16,(ve-v)*h/16]};
   }
   const cube={origin:[el.from[0]-8,el.from[1]+yOffset,el.from[2]-8],size:el.from.map((v,j)=>el.to[j]-v),uv};
   if(cube.size.some(n=>n<=0))throw Error("non-positive cube");
   if(el.rotation){const r=el.rotation;if(!r.origin||r.rescale)throw Error("rotation needs rebake");cube.pivot=[r.origin[0]-8,r.origin[1]+yOffset,r.origin[2]-8];cube.rotation=["x","y","z"].map(a=>a===r.axis?r.angle:0);}
   cubes.push(cube);
  }
  bones.push({name:"piece_"+i,pivot:[0,0,0],cubes});
 }
 if(textureIds.size>1)throw Error("multiple face textures require atlas");
 const description={identifier:opts.identifier||"geometry.minizin.converted",texture_width:w,texture_height:h,visible_bounds_width:3,visible_bounds_height:4,visible_bounds_offset:[0,1,0]};
 return {geometry:{format_version:"1.12.0","minecraft:geometry":[{description,bones}]},texture:[...textureIds][0]||null};
}
function readModel(root,ns,location,stack=[]){
 const [namespace,name]=location.includes(":")?location.split(":",2):[ns,location];
 if(stack.includes(location))throw Error("model parent cycle "+location);
 const rel=path.join("assets",namespace,"models",name+".json");
 const candidates=["common/src/generated/resources","common/src/main/resources","src/generated/resources","src/main/resources"].map(x=>path.join(root,x,rel));
 const file=candidates.find(fs.existsSync);if(!file)throw Error("missing model "+location);
 const m=JSON.parse(fs.readFileSync(file,"utf8"));if(!m.parent)return m;
 return joinModel(readModel(root,ns,m.parent,[...stack,location]),m);
}
const args=process.argv.slice(2);
if(args[0]==="convert"){
 const [root,namespace,id,width,height,output,...specs]=args.slice(1);
 if(!root||!namespace||!id||!output||!specs.length)throw Error("Usage: node tools/java_model_to_bedrock.mjs convert <upstream_root> <namespace> <geo_id> <texture_width> <texture_height> <output.geo.json> <model@offsetY>...");
 const parts=specs.map(spec=>{const sep=spec.lastIndexOf("@");const loc=sep<0?spec:spec.slice(0,sep);const yOffset=sep<0?0:Number(spec.slice(sep+1));return {model:readModel(root,namespace,loc),yOffset};});
 const result=geoFromJava(parts,{identifier:id,width:Number(width),height:Number(height)});
 fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(result.geometry,null,2)+"\n");process.stdout.write(JSON.stringify({path:output,sourceTexture:result.texture,cubes:parts.reduce((n,p)=>n+p.model.elements.length,0)})+"\n");
}
