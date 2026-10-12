/* Sophisticated Backpacks — incremental v2: identity-bound storage.
 * This is NOT the Java container GUI: Bedrock server-ui has no supported
 * API for opening an arbitrary 27-slot native inventory on an item.
 */
import {world,system,ItemStack,EnchantmentTypes} from "@minecraft/server";
import {ActionFormData,ModalFormData} from "@minecraft/server-ui";
const ID="minizin:backpack",IDENT="minizin:backpack_id_v2";
const LEGACY="minizin:personal_backpack_v1",MIGRATION="minizin:backpack_migration_v2";
const CAPACITY=27,MAX_BYTES=30000;
const busyPlayers=new Set(),busyBags=new Set();
const unsupported=new Set(["minecraft:filled_map","minecraft:written_book",
  "minecraft:writable_book","minecraft:potion","minecraft:splash_potion",
  "minecraft:lingering_potion","minecraft:tipped_arrow",
  "minecraft:firework_rocket","minecraft:firework_star","minecraft:banner",
  "minecraft:suspicious_stew"]);
const tell=(p,text)=>p.sendMessage("§b[Mochila]§r "+text);
const invOf=p=>p.getComponent("minecraft:inventory").container;
const dataKey=id=>"minizin:bag_"+id;
const empty=()=>Array(CAPACITY).fill(null);
const safeName=data=>data.name || data.type.split(":").pop().replace(/_/g," ");
const clone=data=>JSON.parse(JSON.stringify(data));
function parse(text,fallback) {try{return typeof text==="string"?JSON.parse(text):fallback;}catch{return fallback;}}
export function encode(item){
  if(item.typeId===ID||item.typeId==="minecraft:bundle"||item.typeId.endsWith("shulker_box"))
    throw Error("Mochilas e contêineres aninhados não são permitidos.");
  if(unsupported.has(item.typeId)||item.getComponent("minecraft:storage_item"))
    throw Error("Os metadados internos deste item não podem ser preservados.");
  const props={};for(const k of item.getDynamicPropertyIds())props[k]=item.getDynamicProperty(k);
  const enchant=item.getComponent("minecraft:enchantable");
  return {type:item.typeId,amount:item.amount,name:item.nameTag,lore:item.getLore(),
    damage:item.getComponent("minecraft:durability")?.damage,
    enchantments:enchant?.getEnchantments().map(x=>({id:x.type.id,level:x.level}))||[],
    keep:item.keepOnDeath,lock:item.lockMode,destroy:item.getCanDestroy(),
    place:item.getCanPlaceOn(),props};
}
export function decode(data){
  const item=new ItemStack(data.type,data.amount);
  if(data.name!==undefined)item.nameTag=data.name;
  item.setLore(data.lore||[]);item.keepOnDeath=data.keep??false;
  if(data.lock)item.lockMode=data.lock;
  item.setCanDestroy(data.destroy||[]);item.setCanPlaceOn(data.place||[]);
  const d=item.getComponent("minecraft:durability");
  if(d&&data.damage!==undefined)d.damage=data.damage;
  const e=item.getComponent("minecraft:enchantable");
  if(e&&(data.enchantments||[]).length)e.addEnchantments(data.enchantments.map(x=>{
    const type=EnchantmentTypes.get(x.id);
    if(!type)throw Error("Encantamento desconhecido: "+x.id);
    return {type,level:x.level};
  }));
  for(const [key,value] of Object.entries(data.props||{}))item.setDynamicProperty(key,value);
  return item;
}
function canonical(value){
  if(Array.isArray(value))return value.map(canonical);
  if(value&&typeof value==="object")return Object.fromEntries(
    Object.keys(value).sort().map(key=>[key,canonical(value[key])]));
  return value;
}
function validate(data){
  // Legacy v1 serialized fields in a different order; compare by value.
  if(JSON.stringify(canonical(encode(decode(data))))!==JSON.stringify(canonical(data)))
    throw Error("Item não preservável: transferência recusada sem alterações.");
}
function getState(id){
  const value=world.getDynamicProperty(dataKey(id));
  const state=parse(value,null);
  if(!state)return {slots:empty(),revision:0};
  if(!Array.isArray(state.slots)||state.slots.length!==CAPACITY)throw Error("Mochila com dados inválidos.");
  return state;
}
function writeState(id,state){
  if(!Array.isArray(state.slots)||state.slots.length!==CAPACITY)throw Error("Capacidade inválida.");
  const raw=JSON.stringify(state);
  if(raw.length>MAX_BYTES)throw Error("Metadados excedem limite do armazenamento.");
  world.setDynamicProperty(dataKey(id),raw);
}
function backpackIn(p,id){
  const inv=invOf(p);
  for(let slot=0;slot<inv.size;slot++){
    const item=inv.getItem(slot);
    if(item?.typeId===ID&&item.getDynamicProperty(IDENT)===id)return {slot,item};
  }
  return null;
}
function assign(p){
  const inv=invOf(p),slot=p.selectedSlotIndex,item=inv.getItem(slot);
  if(item?.typeId!==ID)throw Error("Segure a mochila na mão.");
  let id=item.getDynamicProperty(IDENT);
  if(typeof id==="string"&&id.length>0)return id;
  for(let retry=0;retry<6;retry++){
    id=Array.from({length:4},()=>Math.random().toString(36).slice(2,12)).join("");
    if(world.getDynamicProperty(dataKey(id))!==undefined)continue;
    item.setDynamicProperty(IDENT,id);
    inv.setItem(slot,item);
    writeState(id,{slots:empty(),revision:0});
    return id;
  }
  throw Error("Não foi possível gerar ID único.");
}
function migrateLegacy(p,id){
  const old=parse(p.getDynamicProperty(LEGACY),[]);
  if(!Array.isArray(old)||!old.length)return;
  let destination=p.getDynamicProperty(MIGRATION);
  if(typeof destination!=="string"){
    p.setDynamicProperty(MIGRATION,id);
    destination=id;
  }
  if(destination!==id)return; // Never duplicate old data to a second bag.
  const state=getState(id);
  if(state.revision===0&&state.slots.every(x=>x===null)){
    if(old.length>CAPACITY)throw Error("Armazenamento legado excedeu 27 espaços.");
    for(const payload of old)validate(payload);
    writeState(id,{slots:[...clone(old),...Array(CAPACITY-old.length).fill(null)],revision:1});
  }
  // Retain original player data until the new storage is durable.
  p.setDynamicProperty(LEGACY,undefined);
  p.setDynamicProperty(MIGRATION,undefined);
  tell(p,"Dados antigos migrados para esta mochila. Confira os conteúdos.");
}
async function quantity(p,maximum){
  if(maximum===1)return 1;
  const res=await new ModalFormData().title("Quantidade")
    .slider("Mover itens",1,maximum,{defaultValue:maximum,valueStep:1}).show(p);
  if(res.canceled||!p.isValid)return 0;
  return Math.max(0,Math.min(maximum,Math.floor(Number(res.formValues?.[0])||0)));
}
function assertSession(p,id,revision){
  if(!p.isValid||!backpackIn(p,id))throw Error("Mochila transferida. Abra novamente.");
  const now=getState(id);
  if(now.revision!==revision)throw Error("Mochila modificada em outra sessão.");
  return now;
}
function compatible(left,right){
  // Item data must match exactly apart from count to allow stacking.
  const a=clone(left),b=clone(right);delete a.amount;delete b.amount;
  return JSON.stringify(a)===JSON.stringify(b);
}
function snapshot(inv){
  return Array.from({length:inv.size},(_,i)=>inv.getItem(i));
}
function restore(inv,items){
  items.forEach((item,i)=>inv.setItem(i,item));
}
async function deposit(p,id,slot,revision){
  const inv=invOf(p),choices=[];
  for(let i=0;i<inv.size;i++){
    const item=inv.getItem(i);
    if(!item||item.typeId===ID)continue;
    try{const encoded=encode(item);validate(encoded);choices.push({slot:i,item:encoded});}
    catch{/* Unsupported items are never offered for transfer. */}
  }
  if(!choices.length){tell(p,"Nenhum item transferível disponível.");return;}
  const form=new ActionFormData().title("Guardar no espaço "+(slot+1));
  for(const choice of choices)form.button(safeName(choice.item)+" ×"+choice.item.amount);
  const pick=await form.show(p);
  if(pick.canceled||pick.selection===undefined||!p.isValid)return;
  const choice=choices[pick.selection];if(!choice)return;
  const count=await quantity(p,choice.item.amount);if(!count)return;
  const state=assertSession(p,id,revision);
  const original=inv.getItem(choice.slot);
  if(!original||!compatible(encode(original),choice.item)||original.amount!==choice.item.amount)
    throw Error("Inventário alterado: operação cancelada.");
  const current=state.slots[slot],encoded=encode(original);
  if(current&&!compatible(current,encoded))throw Error("Este espaço contém outro item.");
  const maximum=original.maxAmount;
  if((current?.amount||0)+count>maximum)throw Error("Limite de empilhamento atingido.");
  const payload={...encoded,amount:(current?.amount||0)+count};
  validate(payload);
  const next={slots:[...state.slots],revision:state.revision+1};
  next.slots[slot]=payload;
  const backup=snapshot(inv);
  try{
    if(count===original.amount)inv.setItem(choice.slot,undefined);
    else {original.amount-=count;inv.setItem(choice.slot,original);}
    writeState(id,next);
  }catch(error){restore(inv,backup);throw error;}
  tell(p,"Guardados "+count+" × "+safeName(payload)+".");
}
async function withdraw(p,id,slot,revision){
  const state=assertSession(p,id,revision),payload=state.slots[slot];
  if(!payload)return;
  validate(payload);
  const count=await quantity(p,payload.amount);if(!count)return;
  const latest=assertSession(p,id,revision);
  if(JSON.stringify(latest.slots[slot])!==JSON.stringify(payload))
    throw Error("Este espaço foi alterado.");
  const item=decode({...payload,amount:count});
  const inv=invOf(p),backup=snapshot(inv);
  try{
    const leftover=inv.addItem(item);
    const delivered=count-(leftover?.amount||0);
    if(delivered<=0){tell(p,"Inventário cheio.");return;}
    const next={slots:[...latest.slots],revision:latest.revision+1};
    const remaining=payload.amount-delivered;
    next.slots[slot]=remaining>0?{...payload,amount:remaining}:null;
    writeState(id,next);
    tell(p,"Retirados "+delivered+" × "+safeName(payload)+".");
  }catch(error){restore(inv,backup);throw error;}
}
async function open(p){
  if(busyPlayers.has(p.id))return;
  busyPlayers.add(p.id);
  let id,locked=false;
  try{
    id=assign(p);
    if(busyBags.has(id)){tell(p,"Esta mochila já está sendo usada.");return;}
    busyBags.add(id);locked=true;
    migrateLegacy(p,id);
    const state=getState(id);
    const form=new ActionFormData().title("Mochila • 27 espaços")
      .body("Escolha um espaço. Os dados pertencem a esta mochila, não ao jogador.");
    for(let slot=0;slot<CAPACITY;slot++){
      const item=state.slots[slot];
      form.button(String(slot+1).padStart(2,"0")+"  "+(item?safeName(item)+" ×"+item.amount:"— vazio —"));
    }
    const result=await form.show(p);
    if(result.canceled||result.selection===undefined||!p.isValid)return;
    const slot=result.selection;
    if(slot<0||slot>=CAPACITY)return;
    const current=assertSession(p,id,state.revision).slots[slot];
    if(current){
      const actions=await new ActionFormData().title("Espaço "+(slot+1))
        .body(safeName(current)+" ×"+current.amount)
        .button("Retirar itens").button("Empilhar itens").show(p);
      if(actions.canceled||!p.isValid)return;
      if(actions.selection===0)await withdraw(p,id,slot,state.revision);
      if(actions.selection===1)await deposit(p,id,slot,state.revision);
    }else await deposit(p,id,slot,state.revision);
  }catch(error){tell(p,"Operação não concluída: "+String(error));}
  finally{busyPlayers.delete(p.id);if(locked)busyBags.delete(id);}
}
world.beforeEvents.playerInteractWithBlock.subscribe(e=>{
  if(e.itemStack?.typeId!==ID||e.isFirstEvent===false)return;
  e.cancel=true;system.run(()=>open(e.player));
});
world.beforeEvents.playerInteractWithEntity.subscribe(e=>{
  if(e.itemStack?.typeId!==ID)return;
  e.cancel=true;system.run(()=>open(e.player));
});
world.afterEvents.itemUse.subscribe(({source,itemStack})=>{
  if(itemStack?.typeId===ID)system.run(()=>open(source));
});
