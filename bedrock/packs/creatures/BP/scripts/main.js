import {system,world,safeLoop} from "./core.js";
import {tickDragons,installDragons} from "./dragons.js";
import {tickAtlatitan,installAtlatitan} from "./alex_caves.js";
import {tickIgnis} from "./cataclysm.js";
import {installMowzie} from "./mowzie.js";
import {installEggs,tickEgg} from "./eggs.js";
import {installControls} from "./controls.js";
import {tickUmvuthi} from "./umvuthi.js";
installControls();
installDragons();
installAtlatitan();
installMowzie();
installEggs();
system.runInterval(()=>{
  const tick=system.currentTick;
  safeLoop(e=>{tickDragons(e,tick);tickAtlatitan(e,tick);tickIgnis(e,tick);tickUmvuthi(e,tick);if(tick%20===0)tickEgg(e);});
},10);
