import {world,system,ItemStack,EnchantmentTypes} from '@minecraft/server';
import {ActionFormData} from '@minecraft/server-ui';
const ID='minizin:backpack',KEY='minizin:personal_backpack_v1',LIMIT=27;
const busy=new Set();
const tell=(p,text)=>p.sendMessage('§b[Mochila]§r '+text);
const inventory=p=>p.getComponent('minecraft:inventory').container;
export function encode(item){
  if(item.typeId===ID||item.typeId==='minecraft:bundle'||item.typeId.endsWith('shulker_box'))
    throw new Error('Mochilas e contêineres não podem ser guardados dentro da mochila.');
  if(new Set(['minecraft:filled_map','minecraft:written_book','minecraft:writable_book','minecraft:potion',
    'minecraft:splash_potion','minecraft:lingering_potion','minecraft:tipped_arrow','minecraft:firework_rocket',
    'minecraft:firework_star','minecraft:banner','minecraft:suspicious_stew']).has(item.typeId))
    throw new Error('Este item possui dados internos que esta versão ainda não consegue preservar. Ele fica no inventário.');
  const ench=item.getComponent('minecraft:enchantable'),dur=item.getComponent('minecraft:durability');
  const props={};for(const key of item.getDynamicPropertyIds())props[key]=item.getDynamicProperty(key);
  const data={type:item.typeId,amount:item.amount,lore:item.getLore(),
    keep:item.keepOnDeath,lock:item.lockMode,destroy:item.getCanDestroy(),place:item.getCanPlaceOn(),
    damage:dur?.damage,enchantments:ench?.getEnchantments().map(e=>({id:e.type.id,level:e.level}))??[],props};
  if(item.nameTag!==undefined)data.name=item.nameTag;
  return data;
}
export function decode(data){
  const item=new ItemStack(data.type,data.amount);
  if(data.name!==undefined)item.nameTag=data.name;
  item.setLore(data.lore??[]);item.keepOnDeath=data.keep??false;
  if(data.lock)item.lockMode=data.lock;
  item.setCanDestroy(data.destroy??[]);item.setCanPlaceOn(data.place??[]);
  const dur=item.getComponent('minecraft:durability');if(dur&&data.damage!==undefined)dur.damage=data.damage;
  const ench=item.getComponent('minecraft:enchantable');
  if(ench)ench.addEnchantments((data.enchantments??[]).map(e=>({type:EnchantmentTypes.get(e.id),level:e.level})));
  for(const [key,value] of Object.entries(data.props??{}))item.setDynamicProperty(key,value);
  return item;
}
function read(p){const value=p.getDynamicProperty(KEY);return typeof value==='string'?JSON.parse(value):[];}
function write(p,value){const text=JSON.stringify(value);if(text.length>12000)throw new Error('Limite de metadados da mochila atingido.');p.setDynamicProperty(KEY,text);}
function snapshot(inv){return Array.from({length:inv.size},(_,slot)=>inv.getItem(slot));}
function restore(inv,items){items.forEach((item,slot)=>inv.setItem(slot,item));}
async function open(p){
  if(busy.has(p.id))return;busy.add(p.id);
  try{
    const stored=read(p);
    const action=await new ActionFormData().title('Mochila • '+stored.length+'/'+LIMIT)
      .body('Armazenamento pessoal persistente. Toda mochila deste jogador acessa os mesmos 27 espaços.\nPreserva nomes, encantamentos, durabilidade e propriedades de itens. Contêineres não são aceitos.')
      .button('Guardar uma pilha do inventário').button('Retirar uma pilha da mochila').show(p);
    if(action.canceled||!p.isValid)return;
    const inv=inventory(p);
    if(action.selection===0){
      if(stored.length>=LIMIT){tell(p,'Mochila cheia.');return;}
      const options=[];
      for(let i=0;i<inv.size;i++){const item=inv.getItem(i);if(item&&item.typeId!==ID)options.push({slot:i,item});}
      if(!options.length){tell(p,'Nenhum item para guardar.');return;}
      const form=new ActionFormData().title('Guardar na mochila');
      for(const option of options)form.button((option.item.nameTag??option.item.typeId)+' ×'+option.item.amount);
      const choice=await form.show(p);if(choice.canceled||!p.isValid||choice.selection===undefined)return;
      const option=options[choice.selection];if(!option)return;
      const current=inv.getItem(option.slot);
      if(!current||JSON.stringify(encode(current))!==JSON.stringify(encode(option.item))){tell(p,'O inventário mudou. Abra a mochila novamente.');return;}
      const data=encode(current),fresh=read(p);
      if(fresh.length>=LIMIT){tell(p,'Mochila cheia.');return;}
      const next=[...fresh,data],backup=snapshot(inv);
      // Check serialization and restoration before touching the original stack.
      decode(data);if(JSON.stringify(next).length>12000)throw new Error('Metadados excedem a capacidade.');
      try{inv.setItem(option.slot,undefined);write(p,next);}catch(error){restore(inv,backup);throw error;}
      tell(p,'Pilha guardada.');
    }else if(action.selection===1){
      if(!stored.length){tell(p,'Mochila vazia.');return;}
      const form=new ActionFormData().title('Retirar da mochila');
      for(const data of stored)form.button((data.name??data.type)+' ×'+data.amount);
      const choice=await form.show(p);if(choice.canceled||!p.isValid||choice.selection===undefined)return;
      const fresh=read(p),selected=fresh[choice.selection];
      if(!selected||JSON.stringify(selected)!==JSON.stringify(stored[choice.selection]))return;
      const item=decode(selected),backup=snapshot(inv);
      try{
        const remaining=inv.addItem(item),next=[...fresh];
        if(remaining?.amount===item.amount){tell(p,'Inventário cheio.');return;}
        if(remaining)next[choice.selection]={...selected,amount:remaining.amount};else next.splice(choice.selection,1);
        write(p,next);
      }catch(error){restore(inv,backup);throw error;}
      tell(p,'Pilha retirada.');
    }
  }catch(error){tell(p,'Não foi possível concluir: '+String(error));}
  finally{busy.delete(p.id);}
}
world.beforeEvents.playerInteractWithBlock.subscribe(e=>{
  if(e.itemStack?.typeId!==ID||e.isFirstEvent===false)return;
  e.cancel=true;system.run(()=>open(e.player));
});
world.beforeEvents.playerInteractWithEntity.subscribe(e=>{
  if(e.itemStack?.typeId!==ID)return;e.cancel=true;system.run(()=>open(e.player));
});
world.afterEvents.itemUse.subscribe(({source,itemStack})=>{if(itemStack.typeId===ID)system.run(()=>open(source));});
