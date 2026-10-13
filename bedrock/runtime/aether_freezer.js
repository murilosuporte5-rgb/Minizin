/* Aether Freezer runtime.
 * Java source: FreezingRecipe, FreezerMenu and the nine pinned freezing JSONs.
 * Bedrock has no public API for the native Aether furnace screen, so this uses
 * a persistent one-input/one-output server UI without pretending to be a
 * native container. Item state is serialized before any slot is cleared.
 */
import {world,system,ItemStack} from "@minecraft/server";
import {ActionFormData} from "@minecraft/server-ui";
import {AETHER_FREEZER_RECIPES} from "./aether_freezer_catalog.js";

const BLOCK="minizin_aether:freezer",KEY="minizin:aether_freezer_v1";
const MAX_BYTES=30000,busy=new Set();
const emptyState=(key,dimension,x,y,z)=>({key,dimension,x,y,z,input:null,finish:0,output:null});
function parse(){
  const raw=world.getDynamicProperty(KEY);
  if(raw===undefined)return [];
  const rows=JSON.parse(raw);
  if(!Array.isArray(rows))throw Error("Dados do Freezer inválidos; estado preservado.");
  return rows;
}
function write(rows){
  const raw=JSON.stringify(rows);if(raw.length>MAX_BYTES)throw Error("Limite de Freezers persistentes atingido.");
  world.setDynamicProperty(KEY,raw);
}
function ref(block){
  const p=block.location;return {key:block.dimension.id+":"+Math.floor(p.x)+":"+Math.floor(p.y)+":"+Math.floor(p.z),dimension:block.dimension.id,x:Math.floor(p.x),y:Math.floor(p.y),z:Math.floor(p.z)};
}
function getState(block,rows=parse()){
  const r=ref(block),found=rows.find(x=>x.key===r.key);
  return {rows,state:found??emptyState(r.key,r.dimension,r.x,r.y,r.z)};
}
function encode(item){
  if(!item?.typeId)throw Error("Item ausente.");
  if(item.typeId.endsWith("shulker_box")||item.typeId==="minecraft:bundle")throw Error("Contêineres não são aceitos no slot do Freezer.");
  const props={};for(const key of item.getDynamicPropertyIds?.()||[])props[key]=item.getDynamicProperty(key);
  const data={type:item.typeId,amount:item.amount,lore:item.getLore?.()||[],damage:item.getComponent?.("minecraft:durability")?.damage,props};
  if(item.nameTag!==undefined)data.name=item.nameTag;
  return data;
}
function decode(data){
  if(!data?.type||!Number.isInteger(data.amount)||data.amount<1)throw Error("Item persistido inválido.");
  const item=new ItemStack(data.type,data.amount);
  if(data.name!==undefined)item.nameTag=data.name;
  item.setLore(data.lore||[]);
  const durability=item.getComponent?.("minecraft:durability");if(durability&&data.damage!==undefined)durability.damage=data.damage;
  for(const [key,value] of Object.entries(data.props||{}))item.setDynamicProperty(key,value);
  return item;
}
function recipeFor(item){return AETHER_FREEZER_RECIPES.find(recipe=>recipe.inputs.includes(item?.type));}
function label(data){return data?`${data.name||data.type.split(":").pop().replace(/_/g," ")} x${data.amount}`:"vazio";}
function addToInventory(player,item){
  const inv=player.getComponent("minecraft:inventory")?.container;if(!inv)return false;
  const slot=player.selectedSlotIndex;
  if(!inv.getItem(slot)){inv.setItem(slot,item);return true;}
  const leftover=inv.addItem(item);if(!leftover)return true;
  try{player.dimension.spawnItem(leftover,player.location);return true;}catch{return false;}
}
function persistSwap(player,state,rows,held,replacement,next){
  const inv=player.getComponent("minecraft:inventory")?.container;if(!inv)throw Error("Inventário indisponível.");
  try{inv.setItem(player.selectedSlotIndex,replacement);write(rows.map(x=>x.key===state.key?next:x));}
  catch(error){inv.setItem(player.selectedSlotIndex,held);throw error;}
}
async function open(player,block){
  if(busy.has(player.id))return;busy.add(player.id);
  try{
    const {rows,state}=getState(block),now=world.getAbsoluteTime(),processing=state.finish>now;
    const form=new ActionFormData().title("Aether • Freezer")
      .body(`Entrada: ${label(state.input)}\nSaída: ${label(state.output)}\n${processing?`Processando por mais ${Math.ceil((state.finish-now)/20)}s.` : "Pronto para uma receita Java de congelamento."}`)
      .button("Colocar / trocar entrada").button("Iniciar congelamento").button("Retirar entrada").button("Coletar saída");
    const result=await form.show(player);if(result.canceled||result.selection===undefined||!player.isValid)return;
    const fresh=getState(block).state;if(JSON.stringify(fresh)!==JSON.stringify(state)){player.sendMessage("§eO Freezer mudou; abra novamente para evitar perda.");return;}
    const inv=player.getComponent("minecraft:inventory")?.container;if(!inv)throw Error("Inventário indisponível.");
    const held=inv.getItem(player.selectedSlotIndex);
    if(result.selection===0){
      if(processing){player.sendMessage("§eAguarde o congelamento terminar.");return;}
      if(held){
        const next={...state,input:encode(held)};
        const replacement=state.input?decode(state.input):undefined;
        persistSwap(player,state,rows,held,replacement,next);
        player.sendMessage("§bEntrada do Freezer atualizada; o item anterior voltou para a mão.");
      }else if(state.input){
        const replacement=decode(state.input),next={...state,input:null};
        persistSwap(player,state,rows,held,replacement,next);player.sendMessage("§bEntrada retirada.");
      }else player.sendMessage("§eSegure um item de receita do Freezer.");
      return;
    }
    if(result.selection===1){
      if(state.output){player.sendMessage("§eColete a saída antes de iniciar outra operação.");return;}
      if(!state.input){player.sendMessage("§eNenhuma entrada no Freezer.");return;}
      const recipe=recipeFor(state.input);if(!recipe){player.sendMessage("§eEste item não possui receita Java de congelamento.");return;}
      const next={...state,finish:now+recipe.time};write(rows.map(x=>x.key===state.key?next:x));player.sendMessage(`§bCongelamento iniciado (${recipe.id}, ${recipe.time} ticks).`);return;
    }
    if(result.selection===2){
      if(processing){player.sendMessage("§eAguarde o congelamento terminar.");return;}
      if(!state.input){player.sendMessage("§eA entrada já está vazia.");return;}
      const replacement=decode(state.input),next={...state,input:null};persistSwap(player,state,rows,held,replacement,next);player.sendMessage("§bEntrada retirada.");return;
    }
    if(!state.output){player.sendMessage("§eNenhuma saída pronta.");return;}
    const output=decode(state.output);if(!addToInventory(player,output)){player.sendMessage("§cSem espaço: saída preservada no Freezer.");return;}
    for(const remainder of state.output_remainder||[])addToInventory(player,new ItemStack(remainder.type,remainder.amount));
    const next={...state,output:null,output_remainder:[]};write(rows.map(x=>x.key===state.key?next:x));player.sendMessage("§aSaída coletada sem perda de item.");
  }catch(error){player.sendMessage("§cFreezer: "+String(error));}
  finally{busy.delete(player.id);}
}
function install(){
  world.beforeEvents.playerInteractWithBlock.subscribe(e=>{
    if(e.isFirstEvent===false||e.block?.typeId!==BLOCK)return;
    e.cancel=true;system.run(()=>open(e.player,e.block));
  });
  world.afterEvents.playerBreakBlock.subscribe(e=>{
    if(e.brokenBlockPermutation?.type?.id!==BLOCK)return;
    try{
      const {rows,state}=getState(e.block);for(const data of [state.input,state.output])if(data)try{e.block.dimension.spawnItem(decode(data),e.block.location);}catch{};for(const remainder of state.output_remainder||[])try{e.block.dimension.spawnItem(new ItemStack(remainder.type,remainder.amount),e.block.location);}catch{}
      write(rows.filter(x=>x.key!==state.key));
    }catch(error){console.warn("[Aether Freezer] break recovery "+String(error));}
  });
  system.runInterval(()=>{
    try{
      const rows=parse(),now=world.getAbsoluteTime();let changed=false;
      for(const state of rows){
        if(!state.finish||state.finish>now||state.output||!state.input)continue;
        const recipe=recipeFor(state.input);if(!recipe){state.finish=0;changed=true;continue;}
        const input=decode(state.input);input.amount-=1;
        state.input=input.amount?encode(input):null;state.finish=0;
        state.output=encode(new ItemStack(recipe.output,recipe.count));
        const remainder=recipe.remainder?.[input.typeId];if(remainder){state.output_remainder=state.output_remainder??[];state.output_remainder.push({type:remainder,amount:1});}
        changed=true;
      }
      if(changed)write(rows);
    }catch(error){console.warn("[Aether Freezer] tick "+String(error));}
  },10);
}
install();
