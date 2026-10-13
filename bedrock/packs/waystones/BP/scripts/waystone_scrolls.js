/* Java-backed Waystones scroll family.
 * Source behavior: BlankScrollItem, BoundScrollItem, WarpScrollItem and
 * ReturnScrollItem from mods/15-waystones/upstream. Bedrock stores the bound
 * waystone UID/name on the item stack because it has no Java data component.
 */
import {world,system,ItemStack} from '@minecraft/server';
import {ActionFormData} from '@minecraft/server-ui';
import {travelTo} from './waystones_block.js';

const KEY='minizin:waystones_world_v1',KNOWN='minizin:waystones_known_v1';
const BLANK='minizin:blank_scroll',BOUND='minizin:bound_scroll';
const WARP='minizin:warp_scroll',RETURN='minizin:return_scroll';
const ID='minizin:waystone_id',NAME='minizin:waystone_name';
const busy=new Set(),cooldowns=new Map();
const read=(holder,key)=>{try{const value=holder.getDynamicProperty(key);return typeof value==='string'?JSON.parse(value):[];}catch{return[];}};
const inventory=p=>p.getComponent('minecraft:inventory')?.container;
const creative=p=>String(p.getGameMode?.()??'').toLowerCase()==='creative';
function consumeHeld(player,typeId){
  if(creative(player))return true;
  const inv=inventory(player),slot=player.selectedSlotIndex,item=inv?.getItem(slot);
  if(!item||item.typeId!==typeId)return false;
  if(item.amount<=1)inv.setItem(slot,undefined);else{item.amount--;inv.setItem(slot,item);}
  return true;
}
function addOrDrop(player,item){
  const leftover=inventory(player)?.addItem(item);
  if(leftover)player.dimension.spawnItem(leftover,player.location);
}
function normalize(dim){return dim.startsWith('minecraft:')?dim:'minecraft:'+dim;}
function same(row,block){
  return row.dimension===normalize(block.dimension.id)&&Math.floor(row.x)===Math.floor(block.location.x)&&
    Math.floor(row.y)===Math.floor(block.location.y)&&Math.floor(row.z)===Math.floor(block.location.z);
}
function rowFor(block){return read(world,KEY).find(row=>same(row,block));}
function bind(player,block){
  const row=rowFor(block);
  if(!row){player.sendMessage('§eEste Waystone ainda não foi registrado. Interaja com ele primeiro.');return;}
  const inv=inventory(player),slot=player.selectedSlotIndex,held=inv?.getItem(slot);
  if(!held||held.typeId!==BLANK)return;
  const bound=new ItemStack(BOUND,1);bound.setDynamicProperty(ID,row.id);bound.setDynamicProperty(NAME,row.name);
  bound.nameTag=row.name;
  try{
    if(held.amount===1)inv.setItem(slot,bound);
    else{held.amount--;inv.setItem(slot,held);addOrDrop(player,bound);}
    player.sendMessage('§aPergaminho vinculado: '+row.name+'.');
  }catch(error){player.sendMessage('§cFalha ao vincular pergaminho: '+String(error));}
}
function targets(player,returnOnly=false){
  const known=read(player,KNOWN),rows=read(world,KEY).filter(row=>known.includes(row.id));
  if(!returnOnly)return rows;
  return rows.filter(row=>row.dimension===normalize(player.dimension.id)).sort((a,b)=>{
    const da=(a.x-player.location.x)**2+(a.y-player.location.y)**2+(a.z-player.location.z)**2;
    const db=(b.x-player.location.x)**2+(b.y-player.location.y)**2+(b.z-player.location.z)**2;return da-db;
  }).slice(0,1);
}
async function choose(player,itemId){
  const rows=targets(player);if(!rows.length){player.sendMessage('§eAtive um Waystone interagindo com ele primeiro.');return;}
  const form=new ActionFormData().title('Pergaminho de Teleporte').body('Selecione seu destino:');
  for(const row of rows)form.button(row.name+' §7('+row.dimension.split(':').pop()+')');
  const result=await form.show(player);if(result.canceled||result.selection===undefined||!player.isValid)return;
  const row=rows[result.selection];if(!row)return;
  travelTo(player,row.id,{onComplete:ok=>{if(ok)consumeHeld(player,itemId);}});
}
function boundTarget(player,item){
  const id=item?.getDynamicProperty(ID);
  if(typeof id!=='string'||!id){player.sendMessage('§eEste pergaminho ainda não está vinculado a um Waystone.');return;}
  travelTo(player,id,{requireKnown:false,onComplete:ok=>{if(ok)consumeHeld(player,BOUND);}});
}
function use(player,item){
  if(!player?.isValid||!item)return;
  if(system.currentTick-(cooldowns.get(player.id)??-1000)<200){player.sendMessage('§ePergaminho recarregando (10 segundos).');return;}
  cooldowns.set(player.id,system.currentTick);
  if(item.typeId===BOUND)boundTarget(player,item);
  else if(item.typeId===RETURN){const row=targets(player,true)[0];if(!row){player.sendMessage('§eNenhum Waystone próximo neste mundo.');return;}travelTo(player,row.id,{onComplete:ok=>{if(ok)consumeHeld(player,RETURN);}});}
  else if(item.typeId===WARP)choose(player,WARP);
}
world.beforeEvents.playerInteractWithBlock.subscribe(event=>{
  if(event.isFirstEvent===false||event.itemStack?.typeId!==BLANK)return;
  event.cancel=true;system.run(()=>bind(event.player,event.block));
});
world.afterEvents.itemUse.subscribe(({source,itemStack})=>{
  if(![BOUND,WARP,RETURN].includes(itemStack?.typeId)||busy.has(source.id))return;
  busy.add(source.id);system.run(async()=>{try{use(source,itemStack);}finally{busy.delete(source.id);}});
});
world.afterEvents.playerLeave.subscribe(({playerId})=>{busy.delete(playerId);cooldowns.delete(playerId);});
