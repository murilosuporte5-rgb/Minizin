import {world,system} from "@minecraft/server";
import {tell} from "./core.js";
import {installOrigins,chooseOrigin,currentOrigin} from "./origins.js";
import {installCarryOn,release,recoverBlock} from "./carryon.js";
import {installMCA} from "./mca.js";
import {openMachine} from "./rftools.js";

installOrigins();
installCarryOn();
installMCA();
const help="Comandos: !minizin origins | origem | soltar | recuperar | maquina | ajuda.";
world.beforeEvents.chatSend.subscribe(ev=>{
  const message=ev.message.trim();
  if(!message.toLowerCase().startsWith("!minizin"))return;
  ev.cancel=true;
  const player=ev.sender;
  const command=message.split(/\s+/)[1]?.toLowerCase()||"ajuda";
  system.run(async()=>{
    try{
      if(command==="origins"||command==="origens")await chooseOrigin(player);
      else if(command==="origem")currentOrigin(player);
      else if(command==="soltar"){
        if(!release(player))tell(player,"Você não está carregando um animal.");
      }else if(command==="recuperar"){
        recoverBlock(player);
      }else if(command==="maquina"||command==="máquina")await openMachine(player);
      else tell(player,help);
    }catch(err){tell(player,"Erro: "+String(err));}
  });
});
world.afterEvents.playerSpawn.subscribe(ev=>{
  if(!ev.initialSpawn)return;
  system.run(()=>tell(ev.player,"Pacote de testes ativo. "+help));
});
