import {world,system} from "@minecraft/server";
import {ActionFormData} from "@minecraft/server-ui";
import {tell,hasItem,takeOne,clamp,held,read,write} from "./core.js";
const REP="minizin:mca_relationship_v1";
const busy=new Set();
async function showVillager(player,villager){
  if(busy.has(player.id))return;busy.add(player.id);
  try{
    let relationships=read(villager,REP+"_players",{});
    let value=Number(relationships[player.id]?.value||0);
    const form=new ActionFormData().title("Minizin • MCA Reborn")
      .body("Relacionamento com você.\nAfinidade: "+value)
      .button("Cumprimentar (+1)").button("Conversar (+2)")
      .button("Presentear 1 esmeralda (+5)");
    const result=await form.show(player);
    if(result.canceled||result.selection===undefined||!villager.isValid||!player.isValid)return;
    if(player.dimension.id!==villager.dimension.id||Math.hypot(player.location.x-villager.location.x,
      player.location.y-villager.location.y,player.location.z-villager.location.z)>6)return;
    relationships=read(villager,REP+"_players",{});
    if(!relationships[player.id]&&Object.keys(relationships).length>=64){tell(player,"Limite de relacionamentos deste NPC atingido.");return;}
    const now=world.getAbsoluteTime();
    if(now-Number(relationships[player.id]?.last??-1000)<100){tell(player,"Espere alguns segundos antes da próxima conversa.");return;}
    const old=Number(relationships[player.id]?.value||0);
    const increments=[1,2,5],next=increments[result.selection];
    if(!next)return;
    if(result.selection===2&&!hasItem(player,"minecraft:emerald")){
      tell(player,"Você precisa de 1 esmeralda.");return;
    }
    if(result.selection===2&&!takeOne(player,"minecraft:emerald"))return;
    value=clamp(old+next,0,100);
    relationships[player.id]={value,last:now};
    write(villager,REP+"_players",relationships);
    tell(player,"Afinidade com este aldeão: "+value+"/100.");
  }catch(e){tell(player,"Falha na interação social: "+String(e));}
  finally{busy.delete(player.id);}
}
export function installMCA(){
  world.afterEvents.playerInteractWithEntity.subscribe(event=>{
    if(!event.player.isSneaking)return;
    // Also support the ten experimental MCA NPCs generated from original skin layers.
    const id=event.target.typeId;
    if(id!=="minecraft:villager"&&!/^minizin:mca_(female|male)_[0-4]$/.test(id))return;
    const hand=event.beforeItemStack??event.itemStack??held(event.player);
    if(hand?.typeId!=="minecraft:paper")return;
    system.run(()=>showVillager(event.player,event.target));
  });
}
