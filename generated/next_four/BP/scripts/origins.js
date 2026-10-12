import {world,system} from "@minecraft/server";
import {ActionFormData} from "@minecraft/server-ui";
import {ORIGINS_CATALOG,IMPLEMENTED_PASSIVES} from "./catalog.js";
import {tell} from "./core.js";
const KEY="minizin:origin_v1";
const busy=new Set();
export async function chooseOrigin(player){
  if(busy.has(player.id))return;
  busy.add(player.id);
  try{
    const prev=player.getDynamicProperty(KEY);
    const form=new ActionFormData().title("Minizin • Origins")
      .body("Escolha uma das 10 origens do mod original. Somente quatro possuem um poder passivo de teste; as demais ficam catalogadas.\nAtual: "+(prev??"nenhuma"));
    for(const item of ORIGINS_CATALOG){
      const flag=IMPLEMENTED_PASSIVES[item.id]?"[passivo]":"[catálogo]";
      form.button(item.label+" "+flag);
    }
    const choice=await form.show(player);
    if(choice.canceled||choice.selection===undefined)return;
    const selected=ORIGINS_CATALOG[choice.selection];
    if(!selected)return;
    player.setDynamicProperty(KEY,selected.id);
    tell(player,"Origem selecionada: "+selected.label+". Poderes do Java ainda não foram integralmente portados.");
  }catch(e){tell(player,"Não foi possível abrir Origins: "+String(e));}
  finally{busy.delete(player.id);}
}
export function installOrigins(){
  system.runInterval(()=>{
    for(const player of world.getAllPlayers()){
      try{
        const id=player.getDynamicProperty(KEY);
        const passive=IMPLEMENTED_PASSIVES[id];
        if(!passive)continue;
        player.addEffect(passive.effect,120,{amplifier:0,showParticles:false});
      }catch(e){console.warn("[Minizin Origins] ",String(e));}
    }
  },80);
}
export function currentOrigin(player){
  const id=player.getDynamicProperty(KEY);
  const o=ORIGINS_CATALOG.find(x=>x.id===id);
  tell(player,o?"Sua origem: "+o.label+" ("+(IMPLEMENTED_PASSIVES[id]?"passivo experimental":"sem poderes portados")+")":"Nenhuma origem selecionada. Digite !minizin origins.");
}
