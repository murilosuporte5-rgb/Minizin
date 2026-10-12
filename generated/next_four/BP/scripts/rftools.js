import {world} from "@minecraft/server";
import {ActionFormData} from "@minecraft/server-ui";
import {read,write,tell,hasItem,takeOne,clamp} from "./core.js";
const KEY="minizin:rftools_energy_v1",MAX_ENTRIES=128,MAX_ENERGY=200;
const busy=new Set();
function key(block){const p=block.location;return block.dimension.id+":"+p.x+","+p.y+","+p.z;}
export async function openMachine(player){
  if(busy.has(player.id))return;busy.add(player.id);
  try{
    const hit=player.getBlockFromViewDirection({maxDistance:6});
    if(!hit||hit.block.typeId!=="minecraft:lodestone"){
      tell(player,"Olhe para uma magnetita (lodestone) a até seis blocos.");return;
    }
    const machine=key(hit.block);
    const all=read(world,KEY,{});
    const energy=clamp(Number(all[machine]||0),0,MAX_ENERGY);
    const form=new ActionFormData().title("Minizin • RFTools")
      .body("Célula energética experimental usando magnetita vanilla.\nCarga: "+energy+"/"+MAX_ENERGY)
      .button("Adicionar 1 redstone (+10 energia)")
      .button("Consumir 5 energia (Visão noturna 20s)")
      .button("Consultar carga");
    const r=await form.show(player);
    if(r.canceled||r.selection===undefined)return;
    // Server-side recheck after the async UI, including block still present.
    const check=player.dimension.getBlock(hit.block.location);
    if(check?.typeId!=="minecraft:lodestone"){tell(player,"A máquina não está mais aqui.");return;}
    const now=read(world,KEY,{});
    let current=clamp(Number(now[machine]||0),0,MAX_ENERGY);
    if(r.selection===0){
      if(current+10>MAX_ENERGY){tell(player,"Célula cheia.");return;}
      if(!hasItem(player,"minecraft:redstone")){tell(player,"Falta redstone.");return;}
      if(!takeOne(player,"minecraft:redstone"))return;
      current+=10;
    }else if(r.selection===1){
      if(current<5){tell(player,"Carga insuficiente.");return;}
      player.addEffect("night_vision",400,{amplifier:0,showParticles:false});
      current-=5;
    }else if(r.selection!==2)return;
    now[machine]=current;
    // A capped registry prevents unlimited untrusted world dynamic-property growth.
    if(Object.keys(now).length>MAX_ENTRIES){
      if(!all[machine]){tell(player,"Limite de máquinas atingido.");return;}
    }
    write(world,KEY,now);
    tell(player,"Carga atual: "+current+"/"+MAX_ENERGY);
  }catch(e){tell(player,"Falha na célula energética: "+String(e));}
  finally{busy.delete(player.id);}
}
