// Sourced from the 10 original origin definitions in Origins Fabric.
// The builder can regenerate the names and actual power references from pinned upstream JSON.
export const ORIGINS_CATALOG=[
  {id:"arachnid",label:"Arachnid",powers:["origins:climbing","origins:master_of_webs"]},
  {id:"avian",label:"Avian",powers:["origins:slow_falling","origins:fresh_air"]},
  {id:"blazeborn",label:"Blazeborn",powers:["origins:fire_immunity","origins:water_vulnerability"]},
  {id:"elytrian",label:"Elytrian",powers:["origins:elytra","origins:launch_into_air"]},
  {id:"enderian",label:"Enderian",powers:["origins:throw_ender_pearl","origins:water_vulnerability"]},
  {id:"feline",label:"Feline",powers:["origins:cat_vision","origins:fall_immunity"]},
  {id:"human",label:"Human",powers:[]},
  {id:"merling",label:"Merling",powers:["origins:water_breathing","origins:swim_speed"]},
  {id:"phantom",label:"Phantom",powers:["origins:phantomize","origins:phasing"]},
  {id:"shulk",label:"Shulk",powers:["origins:shulker_inventory","origins:natural_armor"]}
];
export const IMPLEMENTED_PASSIVES={
  avian:{effect:"slow_falling",title:"Queda lenta"},
  blazeborn:{effect:"fire_resistance",title:"Resistência ao fogo"},
  feline:{effect:"night_vision",title:"Visão noturna"},
  merling:{effect:"water_breathing",title:"Respiração aquática"}
};
// All other Apoli/Origins powers remain catalog-only, not ported.
