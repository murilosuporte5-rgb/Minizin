import {world,system,ItemStack} from '@minecraft/server';
import {ActionFormData} from '@minecraft/server-ui';
import {read,write,takeOne,tell,container} from './core.js';

const KEY='minizin:rftools_machines_v2',LIMIT=64,CAPACITY=1000;
const busy=new Set();
const id=b=>b.dimension.id+':'+b.location.x+','+b.location.y+','+b.location.z;
const machine=b=>['minizin_rftools:coalgenerator','minizin_rftools:powercell'].includes(b?.typeId);

/** @param {import('@minecraft/server').Player} player @param {import('@minecraft/server').Block} block */
async function interact(player,block){
  if(busy.has(player.id))return;busy.add(player.id);
  try{
    const key=id(block),all=read(world,KEY,{}),stored=all[key]??{energy:0};
    const result=await new ActionFormData().title('RFTools • '+block.typeId.split(':')[1])
      .body('Energia: '+stored.energy+'/'+CAPACITY+'\nAdaptação Bedrock: combustível e processamento.')
      .button('Gerador: consumir 1 carvão (+160 energia)')
      .button('Processar 1 ferro bruto (−20 energia)')
      .button('Consultar energia').show(player);
    if(result.canceled||result.selection===undefined||!player.isValid)return;
    const current=player.dimension.getBlock(block.location);
    if(player.dimension.id!==block.dimension.id||!machine(current)||current.typeId!==block.typeId||
      Math.hypot(player.location.x-block.location.x,player.location.y-block.location.y,player.location.z-block.location.z)>6)return;
    const now=read(world,KEY,{});
    if(!now[key]&&Object.keys(now).length>=LIMIT){tell(player,'Limite de 64 máquinas registradas.');return;}
    const state=now[key]??{energy:0,dimension:block.dimension.id,location:block.location,type:block.typeId};
    if(result.selection===0){
      if(block.typeId!=='minizin_rftools:coalgenerator'){tell(player,'Abasteça um gerador de carvão.');return;}
      if(state.energy+160>CAPACITY){tell(player,'Gerador cheio.');return;}
      if(!takeOne(player,'minecraft:coal')){tell(player,'Falta carvão.');return;}
      state.energy+=160;
    }else if(result.selection===1){
      if(state.energy<20){tell(player,'Energia insuficiente.');return;}
      const inv=container(player);
      if(!inv||inv.emptySlotsCount<1){tell(player,'Libere um espaço no inventário.');return;}
      if(!takeOne(player,'minecraft:raw_iron')){tell(player,'Falta ferro bruto.');return;}
      try {
        const leftover=inv.addItem(new ItemStack('minecraft:iron_ingot',1));
        if(leftover){inv.addItem(new ItemStack('minecraft:raw_iron',1));return;}
      } catch(error){inv.addItem(new ItemStack('minecraft:raw_iron',1));throw error;}
      state.energy-=20;
    }
    now[key]=state;write(world,KEY,now);
    tell(player,'Energia: '+state.energy+'/'+CAPACITY);
  }catch(error){tell(player,'Erro na máquina: '+String(error));}
  finally{busy.delete(player.id);}
}

world.afterEvents.playerInteractWithBlock.subscribe(({player,block})=>{
  if(machine(block)&&player.isSneaking)system.run(()=>interact(player,block));
});
world.afterEvents.playerBreakBlock.subscribe(({block,dimension})=>{
  const key=dimension.id+':'+block.location.x+','+block.location.y+','+block.location.z;
  const all=read(world,KEY,{});
  if(all[key]){delete all[key];write(world,KEY,all);}
});
// Transfer only within loaded adjacent custom blocks. Persistent coordinate state
// is discarded when the actual block no longer matches; no chunk loading.
system.runInterval(()=>{
  const all=read(world,KEY,{});let changed=false;
  for(const [key,state] of Object.entries(all)){
    try{
      const dimension=world.getDimension(state.dimension),block=dimension.getBlock(state.location);
      if(!block)continue;
      if(block.typeId!==state.type){delete all[key];changed=true;continue;}
      if(state.type!=='minizin_rftools:coalgenerator'||state.energy<=0)continue;
      for(const [x,y,z] of [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]]){
        const neighbor=dimension.getBlock({x:state.location.x+x,y:state.location.y+y,z:state.location.z+z});
        if(neighbor?.typeId!=='minizin_rftools:powercell')continue;
        const nk=id(neighbor);
        if(!all[nk]&&Object.keys(all).length>=LIMIT)continue;
        const target=all[nk]??{energy:0,dimension:state.dimension,location:neighbor.location,type:neighbor.typeId};
        const amount=Math.min(10,state.energy,CAPACITY-target.energy);
        if(amount<=0)continue;
        state.energy-=amount;target.energy+=amount;all[nk]=target;changed=true;
      }
    }catch{} // unloaded chunks are deferred; other dimensions remain isolated
  }
  if(changed)write(world,KEY,all);
},20);
