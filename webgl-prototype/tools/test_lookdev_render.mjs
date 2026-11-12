// 用替身驗證控制流程；不代表 WebGL shader 或視覺驗證。
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import vm from 'node:vm';
const source=readFileSync(new URL('./lookdev_hook.js',import.meta.url),'utf8');
for(const quality of ['high','medium']) {
 let nativeCalls=0, compositeCalls=0, fail=false;
 class Vector {constructor(x=0,y=0){this.x=x;this.y=y;this.z=-20;}set(x,y){this.x=x;this.y=y;return this;}copy(v){Object.assign(this,v);return this;}applyMatrix4(){return this;}}
 const color=(value='#60a8b3')=>({value,set(v){this.value=v;},copy(v){this.value=v.value;},clone(){return color(this.value);}});
 const light=()=>({color:color(),groundColor:color(),shadow:{mapSize:new Vector()}});
 const sprite={visible:true,isSprite:true};
 const scene={background:color(),fog:{color:color()},traverse(fn){fn(sprite);},overrideMaterial:null};
 const camera={near:.1,matrixWorldInverse:{},updateMatrixWorld(){}};
 let target=null, width=800,height=600,ratio=1;
 const renderer={shadowMap:{},autoClear:true,render(){nativeCalls++;},getRenderTarget:()=>target,setRenderTarget(v){target=v;},getSize(v){v.set(width,height);},getPixelRatio:()=>ratio};
 class Pass {constructor(){this.uniforms={focus:{},aperture:{},maxblur:{}};}setSize(w,h){this.size=[w,h];}render(){assert.equal(sprite.visible,false);if(fail)throw Error('GPU mock');}updateGtaoMaterial(p){this.params=p;}}
 class RenderPass extends Pass {render(){renderer.render(scene,camera);}}
 class Composer {constructor(){this.passes=[];}addPass(p){this.passes.push(p);}setPixelRatio(v){this.ratio=v;}setSize(w,h){this.passes.forEach(p=>p.setSize(w*this.ratio,h*this.ratio));}render(){compositeCalls++;this.passes[0].render();this.passes[1].render();if(this.passes[3].enabled)this.passes[3].render();}}
 class ShaderPass extends Pass {constructor(shader){super();this.uniforms=structuredClone(shader.uniforms);this.material={...shader};}}
 const sea={material:{color:color()}};
 const modules={ShaderPass,EffectComposer:Composer,RenderPass,GTAOPass:Pass,UnrealBloomPass:Pass,BokehPass:Pass,OutputPass:Pass};
 const context=vm.createContext({window:{},location:{search:`?quality=${quality}`},URLSearchParams,console,
  THREE:{Vector2:Vector,Vector3:Vector,AgXToneMapping:6,PCFShadowMap:1,SRGBColorSpace:'srgb'},
  sea,renderer,scene,camera,hemi:light(),sun:light(),fill:light(),night:false,lamps:[{}],hospitalNightMaterials:[{material:{},strength:2}],lantern:{},lanternPulse:0,controls:{target:new Vector()},modules});
 const executable=source.replace(/import\('three\/addons\/postprocessing\/([A-Za-z]+)\.js'\)/g,'Promise.resolve({$1:modules.$1})');
 await vm.runInContext(`(async()=>{${executable}})()`,context);
 renderer.render(scene,camera);
 assert.equal(compositeCalls,1);assert.equal(nativeCalls,1);assert.equal(sprite.visible,true);
 const api=context.window.__lookdev;
 assert.equal(api.composer.passes.at(-1),api.passes.grading);
 assert.equal(api.passes.grading.material.toneMapped,false);
 assert.equal(api.passes.grading.uniforms.saturation.value,1.3);
 assert.equal(api.passes.grading.uniforms.contrast.value,1.1);
 assert.equal(api.passes.grading.uniforms.temperature.value,.015);
 assert.equal(renderer.toneMappingExposure,1.4);
 assert.equal(context.hemi.intensity,1.3);
 assert.equal(api.passes.ao.params.radius,.3);
 assert.equal(api.passes.ao.blendIntensity,.4);
 assert.equal(sea.material.color.value,'#42b8d0');
 assert.equal(api.passes.dof.enabled,quality==='high');
 assert.equal(api.passes.ao.size[0],quality==='high'?800:400);
 width=1920;height=1080;renderer.render(scene,camera);
 assert.equal(api.passes.ao.size[1],quality==='high'?1080:540);
 context.night=true;renderer.render(scene,camera);
 assert.equal(api.passes.bloom.threshold,.85);
 assert.equal(api.passes.bloom.strength,.336);
 assert.equal(api.passes.grading.uniforms.saturation.value,1);
 assert.equal(api.passes.grading.uniforms.contrast.value,1);
 assert.equal(api.passes.grading.uniforms.temperature.value,0);
 assert.equal(sea.material.color.value,'#60a8b3');
 api.params.night.grading.temperature=.01;api.refresh();renderer.render(scene,camera);
 assert.equal(api.passes.grading.uniforms.temperature.value,.01);
 context.night=false;renderer.render(scene,camera);
 assert.equal(sea.material.color.value,'#42b8d0');
 assert.equal(api.passes.grading.uniforms.saturation.value,1.3);
 fail=true;assert.throws(()=>renderer.render(scene,camera),/GPU mock/);
 assert.equal(sprite.visible,true);assert.equal(scene.overrideMaterial,null);assert.equal(target,null);
 fail=false;renderer.render(scene,camera);assert.equal(compositeCalls,7);
 target={};renderer.render(scene,camera);assert.equal(compositeCalls,7);
}
console.log('high/medium：遞迴防護、尺寸、日夜調色／海色還原、refresh、例外復原與離屏繞過檢查通過（替身測試）');
