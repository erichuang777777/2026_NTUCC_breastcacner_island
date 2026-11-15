// Shared wall-clock phase: one complete day and night every ten minutes.
export const DAY_CYCLE_MS=600_000;
const smooth=(a,b,x)=>{const t=Math.max(0,Math.min(1,(x-a)/(b-a)));return t*t*(3-2*t);};
export function sampleDayCycle(time,offset=0){
 const phase=((time/DAY_CYCLE_MS+offset)%1+1)%1,angle=phase*Math.PI*2,elevation=Math.cos(angle);
 const daylight=smooth(-.22,.28,elevation);
 return {phase,angle,elevation,daylight,night:daylight<.5,twilight:1-Math.min(1,Math.abs(elevation)/.35)};
}
export function phaseOffset(time,night){return (night?.5:0)-time/DAY_CYCLE_MS;}
