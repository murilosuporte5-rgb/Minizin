import {world,system} from "@minecraft/server";
import {ActionFormData} from "@minecraft/server-ui";
import {tell,hasItem,takeOne,clamp,read,write,held} from "./core.js";

const KEY="minizin:mca_relation_v2",PERSON="minizin:mca_person_v2",
      SPOUSE="minizin:mca_spouse_v2",FAMILY="minizin:mca_family_v2";
const busy=new Set();
function idOf(holder){
  let id=holder.getDynamicProperty(PERSON);
  if(typeof id==="string"&&id.length>6)return id;
  id="mca_"+Date.now().toString(36)+"_"+Math.random().toString(36).slice(2,11);
  holder.setDynamicProperty(PERSON,id);
  return id;
}
function near(p,npc){
  if(!p.isValid||!npc.isValid||p.dimension.id!==npc.dimension.id)return false;
  const a=p.location,b=npc.location;
  return Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z)<=6;
}
function current(npc,pid){
  const all=read(npc,KEY,{});
  return {all,row:all[pid]??{affinity:0,last:-10000,married:false,children:0}};
}
async function show(p,npc){
  if(busy.has(p.id))return;busy.add(p.id);
  try{
    if(!near(p,npc))return;
    const pid=idOf(p),nid=idOf(npc);
    let {row}=current(npc,pid);
    const form=new ActionFormData().title("MCA Reborn • "+(npc.nameTag||"Morador"))
      .body("Afinidade: "+row.affinity+"/100\nEstado: "+(row.married?"Casados":"Solteiros")+
        "\nFilhos: "+row.children)
      .button("Cumprimentar").button("Conversar").button("Presentear esmeralda")
      .button("Pedir em casamento (70 de afinidade)")
      .button("Ter um filho (casamento e 90 de afinidade)");
    const choice=await form.show(p);
    if(choice.canceled||choice.selection===undefined||!near(p,npc))return;
    const action=choice.selection,{all, row:old}=current(npc,pid);
    row={...old};const now=world.getAbsoluteTime();
    if(action<=2){
      if(now-row.last<100){tell(p,"Aguarde 5 segundos antes de conversar novamente.");return;}
      if(action===2&&!hasItem(p,"minecraft:emerald")){tell(p,"Precisa de uma esmeralda.");return;}
      if(Object.keys(all).length>=64&&!all[pid]){tell(p,"NPC com limite de relacionamentos.");return;}
      if(action===2&&!takeOne(p,"minecraft:emerald"))return;
      row.affinity=clamp(row.affinity+[1,3,7][action],0,100);
      row.last=now;all[pid]=row;write(npc,KEY,all);
      tell(p,"Afinidade: "+row.affinity+"/100.");return;
    }
    if(action===3){
      if(row.affinity<70){tell(p,"Precisam se conhecer melhor (70 de afinidade).");return;}
      if(p.getDynamicProperty(SPOUSE)&&p.getDynamicProperty(SPOUSE)!==nid){
        tell(p,"Você já tem um cônjuge neste mundo.");return;
      }
      if(npc.getDynamicProperty(SPOUSE)&&npc.getDynamicProperty(SPOUSE)!==pid){
        tell(p,"Este morador já tem cônjuge.");return;
      }
      row.married=true;all[pid]=row;
      write(npc,KEY,all);
      p.setDynamicProperty(SPOUSE,nid);npc.setDynamicProperty(SPOUSE,pid);
      tell(p,"Casamento registrado com "+(npc.nameTag||"o morador")+".");return;
    }
    if(action!==4)return;
    if(!row.married||p.getDynamicProperty(SPOUSE)!==nid||row.affinity<90){
      tell(p,"Exige casamento e 90 de afinidade.");return;
    }
    if(row.children>=2){tell(p,"Limite de dois filhos por família nesta versão.");return;}
    if(now-Number(row.lastChild??-100000)<24000){
      tell(p,"Aguarde pelo menos um dia de Minecraft.");return;
    }
    const a=npc.location,place={x:Math.floor(a.x)+1.5,y:Math.floor(a.y),z:Math.floor(a.z)+0.5};
    const feet=npc.dimension.getBlock(place),head=npc.dimension.getBlock({...place,y:place.y+1});
    if(!feet?.isAir||!head?.isAir){tell(p,"Libere dois blocos de altura ao lado do morador.");return;}
    let baby;
    try{
      baby=npc.dimension.spawnEntity("minecraft:villager_v2",place,{
        spawnEvent:"minecraft:entity_born",initialPersistence:true
      });
      // Failure to create a real baby cannot become a decorative/adult substitute.
      if(!baby.getComponent("minecraft:ageable"))
        throw Error("A versão Bedrock não ativou o grupo baby/ageable.");
      write(baby,FAMILY,{player:pid,npc:nid});
    }catch(error){
      if(baby?.isValid)baby.remove();
      tell(p,"Nascimento não confirmado: "+String(error));return;
    }
    row.children++;row.lastChild=now;all[pid]=row;write(npc,KEY,all);
    tell(p,"Um aldeão bebê real entrou na família.");
  }catch(error){tell(p,"MCA: "+String(error));}
  finally{busy.delete(p.id);}
}
export function installMCA(){
  world.afterEvents.playerInteractWithEntity.subscribe(e=>{
    if(!e.player.isSneaking)return;
    if(e.target.typeId!=="minecraft:villager"&&e.target.typeId!=="minecraft:villager_v2"
      &&!/^minizin:mca_(female|male)_[0-4]$/.test(e.target.typeId))return;
    const item=e.beforeItemStack??e.itemStack??held(e.player);
    if(item?.typeId!=="minecraft:paper")return;
    system.run(()=>show(e.player,e.target));
  });
  world.afterEvents.playerLeave.subscribe(e=>busy.delete(e.playerId));
}
