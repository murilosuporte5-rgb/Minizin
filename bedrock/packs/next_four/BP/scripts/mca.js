import {world,system} from "@minecraft/server";
import {ActionFormData} from "@minecraft/server-ui";
import {tell,hasItem,takeOne,clamp,held} from "./core.js";
const REP="minizin:mca_relationship_v1";
const busy=new Set();
async function showVillager(player,villager){
  if(busy.has(player.id))return;busy.add(player.id);
  try{
    let value=Number(villager.getDynamicProperty(REP)||0);
    const form=new ActionFormData().title("Minizin • MCA Reborn")
      .body("Aldeão vanilla com relacionamento persistente de teste.\nAfinidade: "+value)
      .button("Cumprimentar (+1)").button("Conversar (+2)")
      .button("Presentear 1 esmeralda (+5)");
    const result=await form.show(player);
    if(result.canceled||result.selection===undefined||!villager.isValid)return;
    const old=Number(villager.getDynamicProperty(REP)||0);
    const increments=[1,2,5],next=increments[result.selection];
    if(!next)return;
    if(result.selection===2&&!hasItem(player,"minecraft:emerald")){
      tell(player,"Você precisa de 1 esmeralda.");return;
    }
    if(result.selection===2&&!takeOne(player,"minecraft:emerald"))return;
    value=clamp(old+next,0,100);
    villager.setDynamicProperty(REP,value);
    tell(player,"Afinidade com este aldeão: "+value+"/100.");
  }catch(e){tell(player,"Falha na interação social: "+String(e));}
  finally{busy.delete(player.id);}
}
export function installMCA(){
  world.afterEvents.playerInteractWithEntity.subscribe(event=>{
    if(event.target.typeId!=="minecraft:villager"||!event.player.isSneaking)return;
    const hand=event.beforeItemStack??event.itemStack??held(event.player);
    if(hand?.typeId!=="minecraft:paper")return;
    system.run(()=>showVillager(event.player,event.target));
  });
}
