// 僅由擷取伺服器附加；參數修改後請同步 JSON 快照。
const LOOKDEV_PARAMS = {
  "quality": "high",
  "toneMapping": "AgX",
  "shadow": {
    "type": "PCFShadowMap",
    "mapSize": 2048,
    "radius": 3,
    "normalBias": 0.02,
    "bias": -0.0001
  },
  "qualityPresets": {
    "high": {
      "aoResolutionScale": 1,
      "aoSamples": 16,
      "dof": true
    },
    "medium": {
      "aoResolutionScale": 0.5,
      "aoSamples": 8,
      "dof": false
    }
  },
  "day": {
    "exposure": 1.4,
    "background": "#c5e4e8",
    "fogNear": 130,
    "fogFar": 280,
    "hemisphere": {
      "sky": "#dceeff",
      "ground": "#8f9971",
      "intensity": 1.3
    },
    "sun": {
      "color": "#ffe0ad",
      "intensity": 3.6
    },
    "fill": {
      "color": "#d4e7ff",
      "intensity": 0.45
    },
    "emissive": {
      "lampIntensity": 1.8,
      "hospitalWindowScale": 0.18,
      "lanternIntensity": 0
    },
    "ao": {
      "radius": 0.3,
      "thickness": 0.4,
      "distanceExponent": 2,
      "distanceFallOff": 1,
      "scale": 1,
      "screenSpaceRadius": false,
      "blendIntensity": 0.4
    },
    "bloom": {
      "threshold": 1.6,
      "strength": 0.22,
      "radius": 0.35
    },
    "dof": {
      "aperture": 8e-05,
      "maxblur": 0.0015
    },
    "grading": {
      "saturation": 1.3,
      "contrast": 1.1,
      "temperature": 0.015
    },
    "seaColor": "#42b8d0"
  },
  "night": {
    "exposure": 1.1,
    "background": "#172e49",
    "fogNear": 130,
    "fogFar": 280,
    "hemisphere": {
      "sky": "#9fbeeb",
      "ground": "#535f68",
      "intensity": 0.5
    },
    "sun": {
      "color": "#b9d3ff",
      "intensity": 0.3
    },
    "fill": {
      "color": "#91b6ed",
      "intensity": 0.24
    },
    "emissive": {
      "lampIntensity": 4,
      "hospitalWindowScale": 1.2,
      "lanternIntensity": 10
    },
    "ao": {
      "radius": 0.65,
      "thickness": 0.8,
      "distanceExponent": 2,
      "distanceFallOff": 1,
      "scale": 1,
      "screenSpaceRadius": false,
      "blendIntensity": 0.5
    },
    "bloom": {
      "threshold": 0.85,
      "strength": 0.336,
      "radius": 0.45
    },
    "dof": {
      "aperture": 6e-05,
      "maxblur": 0.0012
    },
    "grading": {
      "saturation": 1,
      "contrast": 1,
      "temperature": 0
    }
  }
};
{
 const [{EffectComposer}, {RenderPass}, {GTAOPass}, {UnrealBloomPass}, {BokehPass}, {OutputPass}, {ShaderPass}] = await Promise.all([
  import('three/addons/postprocessing/EffectComposer.js'),
  import('three/addons/postprocessing/RenderPass.js'),
  import('three/addons/postprocessing/GTAOPass.js'),
  import('three/addons/postprocessing/UnrealBloomPass.js'),
  import('three/addons/postprocessing/BokehPass.js'),
  import('three/addons/postprocessing/OutputPass.js'),
  import('three/addons/postprocessing/ShaderPass.js')
 ]);
 const query = new URLSearchParams(location.search);
 const quality = query.get('quality') || LOOKDEV_PARAMS.quality;
 if (!Object.hasOwn(LOOKDEV_PARAMS.qualityPresets, quality)) throw new Error('quality 必須是 high 或 medium');
 const q = LOOKDEV_PARAMS.qualityPresets[quality];
 renderer.toneMapping = THREE.AgXToneMapping;
 renderer.outputColorSpace = THREE.SRGBColorSpace;
 // PCFShadowMap 的 radius 有效；PCFSoftShadowMap 不會使用 radius。
 renderer.shadowMap.type = THREE.PCFShadowMap;
 const sh = LOOKDEV_PARAMS.shadow;
 sun.shadow.mapSize.set(sh.mapSize, sh.mapSize);
 Object.assign(sun.shadow, {radius:sh.radius, normalBias:sh.normalBias, bias:sh.bias});
 sun.shadow.map?.dispose(); sun.shadow.map = null;
 renderer.shadowMap.needsUpdate = true;
 const composer = new EffectComposer(renderer);
 const ao = new GTAOPass(scene, camera, 1, 1);
 const resizeAO = ao.setSize.bind(ao);
 ao.setSize = (w,h) => resizeAO(Math.max(1,Math.round(w*q.aoResolutionScale)), Math.max(1,Math.round(h*q.aoResolutionScale)));
 const bloom = new UnrealBloomPass(new THREE.Vector2(1,1));
 const originalSeaColor = sea.material.color.clone();
 // OutputPass 已輸出 sRGB；此處直接調顯示色，不再做 tone mapping 或 sRGB 編碼。
 const grading = new ShaderPass({
  name:'LookdevDisplayGrading',
  uniforms:{tDiffuse:{value:null},saturation:{value:1},contrast:{value:1},temperature:{value:0}},
  vertexShader:`varying vec2 vUv;
   void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
  fragmentShader:`uniform sampler2D tDiffuse;
   uniform float saturation,contrast,temperature;
   varying vec2 vUv;
   void main(){
    vec4 source=texture2D(tDiffuse,vUv);
    float luma=dot(source.rgb,vec3(0.2126,0.7152,0.0722));
    vec3 color=mix(vec3(luma),source.rgb,saturation);
    color=(color-0.5)*contrast+0.5;
    color*=vec3(1.0+temperature,1.0,1.0-temperature);
    gl_FragColor=vec4(clamp(color,0.0,1.0),source.a);
   }`
 });
 grading.material.toneMapped=false;
 const dof = new BokehPass(scene,camera,LOOKDEV_PARAMS.day.dof);
 dof.enabled = q.dof;
 composer.addPass(new RenderPass(scene,camera));
 composer.addPass(ao); composer.addPass(bloom); composer.addPass(dof); composer.addPass(new OutputPass()); composer.addPass(grading);
 // 透明遮罩、海浪、光束與 Sprite 不應在覆寫材質的深度／法線圖中變成實心面。
 for (const pass of [ao,dof]) {
  const renderPass = pass.render.bind(pass);
  pass.render = (...args) => {
   const hidden=[];
   scene.traverse(o => {
    if (o.visible && (o.isSprite || o.isPoints || o.isLine || [o.material].flat().some(m=>m && (m.transparent || m.isShaderMaterial)))) {
     hidden.push(o); o.visible=false;
    }
   });
   try { return renderPass(...args); }
   finally { hidden.forEach(o=>o.visible=true); }
  };
 }
 let presetName;
 function calibrate() {
  const name = night ? 'night' : 'day', p = LOOKDEV_PARAMS[name];
  // 每幀重設光線，避免原動畫／setNight 覆蓋；不對既有值連乘。
  renderer.toneMappingExposure=p.exposure;
  scene.background.set(p.background);
  if(scene.fog) { scene.fog.color.set(p.background); scene.fog.near=p.fogNear; scene.fog.far=p.fogFar; }
  hemi.color.set(p.hemisphere.sky); hemi.groundColor.set(p.hemisphere.ground); hemi.intensity=p.hemisphere.intensity;
  sun.color.set(p.sun.color); sun.intensity=p.sun.intensity;
  fill.color.set(p.fill.color); fill.intensity=p.fill.intensity;
  lamps.forEach(m=>m.emissiveIntensity=p.emissive.lampIntensity);
  hospitalNightMaterials.forEach(({material,strength})=>material.emissiveIntensity=strength*p.emissive.hospitalWindowScale);
  lantern.intensity=p.emissive.lanternIntensity + lanternPulse*5;
  if (presetName!==name) {
   ao.updateGtaoMaterial({...p.ao,samples:q.aoSamples}); ao.blendIntensity=p.ao.blendIntensity;
   Object.assign(bloom,p.bloom);
   for(const key of ['saturation','contrast','temperature']) grading.uniforms[key].value=p.grading[key];
   if(name==='day') sea.material.color.set(p.seaColor);
   else sea.material.color.copy(originalSeaColor);
   dof.uniforms.aperture.value=p.dof.aperture; dof.uniforms.maxblur.value=p.dof.maxblur;
   presetName=name;
  }
 }
 const nativeRender=renderer.render.bind(renderer), size=new THREE.Vector2(), focus=new THREE.Vector3();
 let insideComposer=false, lastWidth=0, lastHeight=0, lastRatio=0;
 renderer.render = function(renderScene,renderCamera) {
  if (insideComposer || renderScene!==scene || renderCamera!==camera || renderer.getRenderTarget()!==null) return nativeRender(renderScene,renderCamera);
  calibrate();
  renderer.getSize(size); const ratio=renderer.getPixelRatio();
  if(size.x!==lastWidth || size.y!==lastHeight || ratio!==lastRatio) {
   composer.setPixelRatio(ratio); composer.setSize(size.x,size.y);
   lastWidth=size.x; lastHeight=size.y; lastRatio=ratio;
  }
  camera.updateMatrixWorld(true);
  // Bokeh 的 focus 是相機空間深度，不是斜向的歐氏距離。
  dof.uniforms.focus.value=Math.max(camera.near,-focus.copy(controls.target).applyMatrix4(camera.matrixWorldInverse).z);
  const oldOverride=scene.overrideMaterial, oldTarget=renderer.getRenderTarget(), oldAutoClear=renderer.autoClear;
  insideComposer=true;
  try { composer.render(); }
  finally { insideComposer=false; scene.overrideMaterial=oldOverride; renderer.setRenderTarget(oldTarget); renderer.autoClear=oldAutoClear; }
 };
 window.__lookdev={quality,params:LOOKDEV_PARAMS,composer,passes:{ao,bloom,dof,grading},refresh:()=>{presetName=undefined;}};
}
