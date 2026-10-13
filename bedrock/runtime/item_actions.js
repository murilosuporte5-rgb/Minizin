import {world,system} from '@minecraft/server';
import {chooseOrigin} from './origins/origins.js';
import {container,read,write,tell} from './mca/core.js';

const relationshipKey='minizin:mca_relationship_v1_players';
const pairKey='minizin:mca_pair_v1';
const rings=new Map([
  ['minizin:mca_item_engagement_ring','engaged'],['minizin:mca_item_engagement_ring_rg','engaged'],
  ['minizin:mca_item_wedding_ring','married'],['minizin:mca_item_wedding_ring_rg','married']
]);
const isNpc=e=>/^minizin:mca_(female|male)_[0-4]$/.test(e.typeId);
const inRange=(p,e)=>p.isValid&&e.isValid&&p.dimension.id===e.dimension.id&&
  Math.hypot(p.location.x-e.location.x,p.location.y-e.location.y,p.location.z-e.location.z)<=6;

function offerRing(player,npc,itemId){
  if(!inRange(player,npc)||!isNpc(npc))return;
  const stage=rings.get(itemId),threshold=stage==='married'?100:50;
  const value=Number(read(npc,relationshipKey,{})[player.id]?.value||0);
  const npcPair=read(npc,pairKey,{}),playerPair=read(player,pairKey,{});
  if(npcPair.partner&&npcPair.partner!==player.id){tell(player,'Este NPC já possui um relacionamento.');return;}
  if(playerPair.partner&&playerPair.partner!==npc.id){tell(player,'Você já possui um relacionamento com outro NPC.');return;}
  if(npcPair.stage===stage||npcPair.stage==='married'){tell(player,'Este relacionamento já foi registrado.');return;}
  if(value<threshold){tell(player,'Afinidade insuficiente: '+value+'/'+threshold+'. Converse e presenteie este NPC primeiro.');return;}
  const inv=container(player),slot=player.selectedSlotIndex,item=inv?.getItem(slot);
  if(item?.typeId!==itemId)return;
  // Persist both sides before consuming the held ring; restore on write failure.
  try{
    write(npc,pairKey,{partner:player.id,stage});write(player,pairKey,{partner:npc.id,stage});
  }catch(error){write(npc,pairKey,npcPair);write(player,pairKey,playerPair);throw error;}
  if(item.amount===1)inv.setItem(slot,undefined);else{item.amount--;inv.setItem(slot,item);}
  tell(player,stage==='married'?'Casamento registrado com este NPC.':'Noivado registrado com este NPC.');
}

world.beforeEvents.playerInteractWithEntity.subscribe(event=>{
  const id=event.itemStack?.typeId;
  if(!rings.has(id)||!isNpc(event.target))return;
  event.cancel=true;
  system.run(()=>{try{offerRing(event.player,event.target,id);}catch(e){tell(event.player,'Falha no anel: '+String(e));}});
});
const orb='minizin:origins_item_orb_of_origin';
world.beforeEvents.playerInteractWithBlock.subscribe(event=>{
  if(event.itemStack?.typeId!==orb||event.isFirstEvent===false)return;
  event.cancel=true;system.run(()=>chooseOrigin(event.player));
});
world.beforeEvents.playerInteractWithEntity.subscribe(event=>{
  if(event.itemStack?.typeId!==orb)return;
  event.cancel=true;system.run(()=>chooseOrigin(event.player));
});
world.afterEvents.itemUse.subscribe(({source,itemStack})=>{
  if(itemStack.typeId===orb)system.run(()=>chooseOrigin(source));
});
