export const PREFIX="§b[Minizin]§r ";
export function tell(player,msg){try{player.sendMessage(PREFIX+msg);}catch(e){console.warn("[Minizin] chat",String(e));}}
export function held(player){
  try{const c=player.getComponent("minecraft:inventory").container;
      return c?.getItem(player.selectedSlotIndex);}catch{return undefined;}
}
export function container(player){return player.getComponent("minecraft:inventory")?.container;}
export function takeOne(player,id){
  const inv=container(player);if(!inv)return false;
  for(let i=0;i<inv.size;i++){
    const item=inv.getItem(i);
    if(item?.typeId!==id||item.amount<=0)continue;
    if(item.amount===1)inv.setItem(i,undefined);
    else{item.amount--;inv.setItem(i,item);}
    return true;
  }
  return false;
}
export function hasItem(player,id){
  const inv=container(player);if(!inv)return false;
  for(let i=0;i<inv.size;i++){if(inv.getItem(i)?.typeId===id)return true;}
  return false;
}
export function read(holder,key,fallback){
  try{const v=holder.getDynamicProperty(key);
      if(typeof v!=="string")return fallback;
      const data=JSON.parse(v);return data??fallback;}catch{return fallback;}
}
export function write(holder,key,value){holder.setDynamicProperty(key,JSON.stringify(value));}
export function clamp(n,min,max){return Math.max(min,Math.min(max,n));}
