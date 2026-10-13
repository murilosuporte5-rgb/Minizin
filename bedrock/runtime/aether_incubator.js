/* Aether Incubator runtime.
 * Java source: IncubatorMenu, IncubatorBlockEntity and three
 * IncubationRecipe JSONs. Bedrock has no public native menu equivalent, so
 * the persistent two-slot server UI exposes the same input/fuel/progress
 * contract without claiming to be the Java screen.
 */
import {world,system,ItemStack} from "@minecraft/server";
import {ActionFormData} from "@minecraft/server-ui";
import {AETHER_INCUBATOR_RECIPES,AETHER_INCUBATOR_FUEL} from "./aether_incubator_catalog.js";

const BLOCK="minizin_aether:incubator",KEY="minizin:aether_incubator_v1",MAX_BYTES=30000,busy=new Set();
const emptyState=(key,dimension,x,y,z)=>({key,dimension,x,y,z,input:null,fuel:null,finish:0,moaType:null});
function parse(){const raw=world.getDynamicProperty(KEY);if(raw===undefined)return [];const rows=JSON.parse(raw);if(!Array.isArray(rows))throw Error("Dados do Incubator inválidos; estado preservado.");return rows;}
function write(rows){const raw=JSON.stringify(rows);if(raw.length>MAX_BYTES)throw Error("Limite de Incubators persistentes atingido.");world.setDynamicProperty(KEY,raw);}
function ref(block){const p=block.location;return {key:block.dimension.id+":"+Math.floor(p.x)+":"+Math.floor(p.y)+":"+Math.floor(p.z),dimension:block.dimension.id,x:Math.floor(p.x),y:Math.floor(p.y),z:Math.floor(p.z)};}
function stateAt(block,rows=parse()){const r=ref(block);return {rows,state:rows.find(x=>x.key===r.key)??emptyState(r.key,r.dimension,r.x,r.y,r.z)};}
function encode(item){if(!item?.typeId)throw Error("Item ausente.");return {type:item.typeId,amount:item.amount,name:item.nameTag,lore:item.getLore?.()||[],damage:item.getComponent?.("minecraft:durability")?.damage};}
function decode(data){if(!data?.type||!Number.isInteger(data.amount)||data.amount<1)throw Error("Item persistido inválido.");const item=new ItemStack(data.type,data.amount);if(data.name!==undefined)item.nameTag=data.name;item.setLore(data.lore||[]);const d=item.getComponent?.("minecraft:durability");if(d&&data.damage!==undefined)d.damage=data.damage;return item;}
function findRecipe(data){return AETHER_INCUBATOR_RECIPES.find(x=>x.input===data?.type);}
function label(data){return data?`${data.name||data.type.split(":").pop().replace(/_/g," ")} x${data.amount}`:"vazio";}
function addToInventory(player,item){const inv=player.getComponent("minecraft:inventory")?.container;if(!inv)return false;const slot=player.selectedSlotIndex;if(!inv.getItem(slot)){inv.setItem(slot,item);return true;}const rest=inv.addItem(item);if(!rest)return true;try{player.dimension.spawnItem(rest,player.location);return true;}catch{return false;}}
function replaceHeld(player,held,replacement,rows,state,next){const inv=player.getComponent("minecraft:inventory")?.container;if(!inv)throw Error("Inventário indisponível.");try{inv.setItem(player.selectedSlotIndex,replacement);write(rows.map(x=>x.key===state.key?next:x));}catch(error){inv.setItem(player.selectedSlotIndex,held);throw error;}}
async function open(player,block){if(busy.has(player.id))return;busy.add(player.id);try{
  const {rows,state}=stateAt(block),now=world.getAbsoluteTime(),processing=state.finish>now;
  const form=new ActionFormData().title("Aether • Incubator").body(`Ovo: ${label(state.input)}\nCombustível: ${label(state.fuel)}\n${processing?`Incubando por mais ${Math.ceil((state.finish-now)/20)}s.`:"Receita Java: 1000 ticks; combustível Java: 500 ticks."}`)
    .button("Colocar / trocar ovo").button("Colocar / trocar combustível").button("Iniciar incubação").button("Retirar ovo").button("Retirar combustível");
  const result=await form.show(player);if(result.canceled||result.selection===undefined||!player.isValid)return;
  const fresh=stateAt(block).state;if(JSON.stringify(fresh)!==JSON.stringify(state)){player.sendMessage("§eO Incubator mudou; abra novamente para evitar perda.");return;}
  const inv=player.getComponent("minecraft:inventory")?.container;if(!inv)throw Error("Inventário indisponível.");const held=inv.getItem(player.selectedSlotIndex);
  if(result.selection===0){if(processing){player.sendMessage("§eAguarde a incubação terminar.");return;}if(!held){player.sendMessage("§eSegure um ovo de Moa.");return;}const next={...state,input:encode(held)},replacement=state.input?decode(state.input):undefined;replaceHeld(player,held,replacement,rows,state,next);return;}
  if(result.selection===1){if(processing){player.sendMessage("§eAguarde a incubação terminar.");return;}if(!held||!AETHER_INCUBATOR_FUEL[held.typeId]){player.sendMessage("§eSegure uma tocha de Ambrosium.");return;}const next={...state,fuel:encode(held)},replacement=state.fuel?decode(state.fuel):undefined;replaceHeld(player,held,replacement,rows,state,next);return;}
  if(result.selection===2){if(processing){player.sendMessage("§eA incubação já está em andamento.");return;}const recipe=findRecipe(state.input);if(!recipe){player.sendMessage("§eOvo sem receita Java de incubação.");return;}if(!state.fuel||!AETHER_INCUBATOR_FUEL[state.fuel.type]){player.sendMessage("§eCombustível insuficiente: tocha de Ambrosium.");return;}const fuel=decode(state.fuel);fuel.amount--;const next={...state,fuel:fuel.amount?encode(fuel):null,finish:now+recipe.time,moaType:recipe.moaType};write(rows.map(x=>x.key===state.key?next:x));player.sendMessage(`§bIncubação iniciada (${recipe.id}, ${recipe.time} ticks).`);return;}
  if(result.selection===3){if(processing||!state.input){player.sendMessage(processing?"§eAguarde a incubação terminar.":"§eO slot de ovo já está vazio.");return;}const replacement=decode(state.input);replaceHeld(player,held,replacement,rows,state,{...state,input:null});return;}
  if(processing||!state.fuel){player.sendMessage(processing?"§eAguarde a incubação terminar.":"§eO slot de combustível já está vazio.");return;}replaceHeld(player,held,decode(state.fuel),rows,state,{...state,fuel:null});
 }catch(error){player.sendMessage("§cIncubator: "+String(error));}finally{busy.delete(player.id);}}
function install(){
  world.beforeEvents.playerInteractWithBlock.subscribe(e=>{if(e.isFirstEvent===false||e.block?.typeId!==BLOCK)return;e.cancel=true;system.run(()=>open(e.player,e.block));});
  world.afterEvents.playerBreakBlock.subscribe(e=>{if(e.brokenBlockPermutation?.type?.id!==BLOCK)return;try{const {rows,state}=stateAt(e.block);for(const data of [state.input,state.fuel])if(data)try{e.block.dimension.spawnItem(decode(data),e.block.location);}catch{}write(rows.filter(x=>x.key!==state.key));}catch(error){console.warn("[Aether Incubator] break recovery "+String(error));}});
  system.runInterval(()=>{try{const rows=parse(),now=world.getAbsoluteTime();let changed=false;for(const state of rows){if(!state.finish||state.finish>now||!state.input)continue;const recipe=findRecipe(state.input);if(!recipe){state.finish=0;changed=true;continue;}const input=decode(state.input);input.amount--;const pos={x:state.x+.5,y:state.y+1.05,z:state.z+.5};let entity;try{entity=world.getDimension(state.dimension).spawnEntity("minizin_aether:moa",pos);}catch(error){console.warn("[Aether Incubator] spawn deferred "+String(error));continue;}entity.setDynamicProperty("minizin:moa_type",recipe.moaType);entity.setDynamicProperty("minizin:moa_is_baby",true);entity.setDynamicProperty("minizin:moa_hungry",true);entity.setDynamicProperty("minizin:moa_player_grown",true);state.input=input.amount?encode(input):null;state.finish=0;state.moaType=null;changed=true;}if(changed)write(rows);}catch(error){console.warn("[Aether Incubator] tick "+String(error));}},10);
}
install();
