import {world,system} from '@minecraft/server';
import {ActionFormData} from '@minecraft/server-ui';
const KEY='minizin:waystones_world_v1',KNOWN='minizin:waystones_known_v1';
const busy=new Set(),cooldowns=new Map();
function read(holder,key){const value=holder.getDynamicProperty(key);try{return typeof value==='string'?JSON.parse(value):[];}catch{return[];}}
async function travel(player){
  if(busy.has(player.id))return;busy.add(player.id);
  try{
    if(system.currentTick-(cooldowns.get(player.id)??-1000)<200){player.sendMessage('§ePedra recarregando (10 segundos).');return;}
    const known=read(player,KNOWN),records=read(world,KEY).filter(record=>known.includes(record.id));
    if(!records.length){player.sendMessage('§eAtive um Waystone interagindo com ele primeiro.');return;}
    const form=new ActionFormData().title('Pedra de teleporte • Waystones');
    for(const record of records)form.button(record.name+' ('+record.dimension+')');
    const result=await form.show(player);if(result.canceled||result.selection===undefined||!player.isValid)return;
    const chosen=records[result.selection];
    if(!chosen||!read(player,KNOWN).includes(chosen.id))return;
    const current=read(world,KEY).find(row=>row.id===chosen.id);if(!current)return;
    const dimension=world.getDimension(current.dimension);
    const anchor={x:Math.floor(current.x),y:Math.floor(current.y),z:Math.floor(current.z)};
    // A persistent coordinate without a surviving block is not a valid destination.
    if(dimension.getBlock(anchor)?.typeId!=='minizin:andesite_waystone_block'){
      player.sendMessage('§eO marco não está carregado ou foi removido.');return;
    }
    for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1]]){
      const at={x:anchor.x+dx+0.5,y:anchor.y,z:anchor.z+dz+0.5};
      try{
        if(!dimension.getBlock(at)?.isAir||!dimension.getBlock({...at,y:at.y+1})?.isAir)continue;
        const floor=dimension.getBlock({...at,y:at.y-1});if(!floor||floor.isAir||floor.isLiquid)continue;
        player.teleport(at,{dimension,checkForBlocks:true});cooldowns.set(player.id,system.currentTick);return;
      }catch{}
    }
    player.sendMessage('§eDestino descarregado ou bloqueado. Use o próprio Waystone para testar o trajeto.');
  }catch(error){player.sendMessage('§cWaystones: '+String(error));}
  finally{busy.delete(player.id);}
}
world.beforeEvents.playerInteractWithBlock.subscribe(e=>{
  if(e.itemStack?.typeId!=='minizin:warp_stone'||e.isFirstEvent===false)return;
  e.cancel=true;system.run(()=>travel(e.player));
});
world.afterEvents.entityDie.subscribe(({deadEntity})=>{
  if(deadEntity.typeId!=='minizin:andesite_waystone')return;
  try{const id=deadEntity.getDynamicProperty('minizin:waystone_id');
    world.setDynamicProperty(KEY,JSON.stringify(read(world,KEY).filter(row=>row.id!==id)));}catch{}
});
world.afterEvents.playerLeave.subscribe(({playerId})=>cooldowns.delete(playerId));
