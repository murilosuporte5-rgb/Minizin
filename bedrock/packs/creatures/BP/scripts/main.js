import {system,world,safeLoop} from "./core.js";
import {tickDragons,installDragons} from "./dragons.js";
import {tickAtlatitan,installAtlatitan} from "./alex_caves.js";
import {tickIgnis} from "./cataclysm.js";
import {installMowzie} from "./mowzie.js";
installDragons();
installAtlatitan();
installMowzie();
system.runInterval(()=>{
  const tick=system.currentTick;
  safeLoop(e=>{tickDragons(e,tick);tickAtlatitan(e,tick);tickIgnis(e,tick);});
},10);
