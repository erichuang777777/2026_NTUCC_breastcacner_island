"""Reproducible, fully three-dimensional shared cast. Blender coordinates from Y-up authoring.
All six roles share a 18-bone rig, deformation weights and action timing.
"""
from pathlib import Path
import math, json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / 'webgl-prototype/assets/characters/v06'
OUT.mkdir(parents=True, exist_ok=True)
ROLES = [('visitor','#35363a','#454955','#797a80'),('scarf','#31394f','#5e6370','#262522'),('doctor','#f0f0ee','#4a505d','#282929'),('nurse','#303e6a','#303e6a','#292522'),('surgeon','#eff0ee','#3b4050','#464546'),('scrub','#39756b','#39756b','#654738')]

def xyz(p): return (p[0],-p[2],p[1])
def linear(v): return v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4

def mat(name,hex,rough=.72):
    c=tuple(linear(int(hex[i:i+2],16)/255) for i in (1,3,5))
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=rough
    if name in ('shirt','pants','headscarf','cream'):
        # Packed micro-weave roughness texture; uses authored UVs, no runtime noise shader.
        image=bpy.data.images.new(name+'-weave',width=64,height=64)
        pixels=[]
        for y in range(64):
            for x in range(64):
                v=.72+.10*math.sin(x*math.pi/2)*math.sin(y*math.pi/2)
                pixels.extend((v,v,v,1))
        image.pixels=pixels;image.pack();image.colorspace_settings.name='Non-Color'
        texture=m.node_tree.nodes.new('ShaderNodeTexImage');texture.image=image
        m.node_tree.links.new(texture.outputs['Color'],bs.inputs['Roughness'])
    return m

parts=[]; category='body'
def register(o,name,m,bone='head',weights=None):
    o.name=name;o.data.materials.append(m)
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    for v in o.data.vertices:
        w=weights(v.co.z) if weights else {bone:1}
        for n,value in w.items():
            if value>0:
                vg=o.vertex_groups.get(n) or o.vertex_groups.new(name=n);vg.add([v.index],value,'REPLACE')
    parts.append((o,category));o.select_set(False)
    return o

def ell(name,p,s,m,bone='head',segments=20):
    bpy.ops.object.select_all(action='DESELECT');bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=12,location=xyz(p))
    o=bpy.context.object;o.scale=(s[0],s[2],s[1]);return register(o,name,m,bone)

def curve(name,pts,r,m,bone='head'):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=8;c.bevel_depth=r;c.bevel_resolution=2
    sp=c.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
    for b,p in zip(sp.bezier_points,pts):b.co=xyz(p);b.handle_left_type='AUTO';b.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
    return register(bpy.context.object,name,m,bone)

def loft(name,rings,m,bone='hips',weights=None):
    # Elliptical sections produce continuous shoulders, sleeves and trousers.
    verts=[];faces=[];n=24
    for x,y,z,rx,rz in rings:
        for k in range(n):
            a=k*math.tau/n;verts.append(xyz((x+math.cos(a)*rx,y,z+math.sin(a)*rz)))
    for j in range(len(rings)-1):
        for k in range(n):a=j*n+k;b=j*n+(k+1)%n;faces.append((a,b,b+n,a+n))
    faces.extend([tuple(reversed(range(n))),tuple((len(rings)-1)*n+k for k in range(n))])
    g=bpy.data.meshes.new(name);g.from_pydata(verts,[],faces);g.update()
    uv=g.uv_layers.new(name='ClothUV')
    for face in g.polygons:
        seam=any(g.loops[i].vertex_index%n==n-1 for i in face.loop_indices)
        for i in face.loop_indices:
            index=g.loops[i].vertex_index;k=index%n
            uv.data[i].uv=(1 if seam and k==0 else k/n,(index//n)/max(1,len(rings)-1))
    o=bpy.data.objects.new(name,g);bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    mod=o.modifiers.new('Soft tailored silhouette','SUBSURF');mod.levels=1;bpy.ops.object.modifier_apply(modifier=mod.name)
    return register(o,name,m,bone,weights)

def joint(upper,lower,y,span=.09):
    def weights(h):
        t=max(0,min(1,(h-y+span/2)/span));t=t*t*(3-2*t)
        return {upper:t,lower:1-t}
    return weights

metrics=[]
for ri,(role,shirt_hex,pants_hex,hair_hex) in enumerate(ROLES):
    bpy.ops.wm.read_factory_settings(use_empty=True);parts=[];category='body'
    skin=mat('skin','#edc6a7');blush=mat('blush','#dea294');outfit=mat('shirt',shirt_hex);pants=mat('pants',pants_hex);hair=mat('hair',hair_hex)
    cream=mat('cream','#64656a' if ri<2 else '#fff4df');white=mat('shoe','#fbf8ec');sole=mat('sole','#d2c6af');ink=mat('ink','#342820',.48);iris=mat('iris','#805b3b',.35);eye_white=mat('eye-white','#fff9f0',.28);rose=mat('ribbon','#d77894');metal=mat('metal','#9aa9aa',.3);scarf=mat('headscarf',hair_hex)
    # Continuous face, neck, torso and hips; face features are real geometry.
    ell('face',(0,1.245,0),(.226,.255,.203),skin,segments=32)
    ell('neck',(0,1.005,0),(.075,.106,.077),skin,'spine')
    loft('shirt-body',[(0,.58,0,.14,.10),(0,.60,0,.17,.115),(0,.76,0,.166,.12),(0,.93,0,.194,.117),(0,.987,0,.14,.10),(0,1.005,0,.095,.074)],outfit if ri>=2 else cream,'spine')
    ell('hips',(0,.565,0),(.148,.092,.109),pants,'hips')
    for sign,side in [(-1,'L'),(1,'R')]:
        ell('ear-'+side,(sign*.225,1.23,-.004),(.043,.067,.033),skin)
        ell('ear-inner-'+side,(sign*.236,1.23,.023),(.020,.038,.011),blush)
        x=sign*.086
        ell('eye-white-'+side,(x,1.267,.184),(.052,.062,.031),eye_white,'eye.'+side)
        ell('iris-'+side,(x,1.267,.210),(.030,.038,.016),iris,'eye.'+side)
        ell('pupil-'+side,(x,1.267,.223),(.017,.025,.008),ink,'eye.'+side)
        ell('glint-'+side,(x-.012,1.286,.230),(.010,.012,.004),white,'eye.'+side,16)
        ell('glint-small-'+side,(x+.012,1.253,.230),(.004,.005,.003),white,'eye.'+side,12)
        curve('upper-lash-'+side,[(x-.047,1.272,.209),(x,1.326,.198),(x+.047,1.277,.209)],.005,hair)
        curve('lower-eyelid-'+side,[(x-.044,1.253,.203),(x,1.209,.200),(x+.044,1.253,.203)],.003,skin)
        curve('lid-fold-'+side,[(x-.048,1.282,.197),(x,1.334,.184),(x+.048,1.282,.197)],.0035,skin)
        curve('brow-'+side,[(x-.035,1.350,.180),(x,1.355,.188),(x+.034,1.345,.183)],.009,hair)
        ell('cheek-'+side,(sign*.15,1.205,.160),(.034,.016,.008),blush)
        # Smoothly weighted knee and elbow sections, not separated blocks.
        x=sign*.092
        loft('trousers-'+side,[(x,.10,0,.060,.064),(x,.13,0,.064,.070),(x,.27,0,.063,.073),(x,.34,0,.069,.077),(x,.48,0,.077,.090),(x,.58,0,.080,.090)],pants,weights=joint('thigh.'+side,'shin.'+side,.32))
        curve('trouser-seam-'+side,[(x+sign*.066,.14,.016),(x+sign*.069,.29,.016),(x+sign*.079,.50,.016)],.0025,sole,'thigh.'+side)
        ell('sneaker-'+side,(x,.065,.038),(.077,.062,.128),white,'foot.'+side)
        ell('rubber-sole-'+side,(x,.022,.040),(.079,.021,.130),sole,'foot.'+side)
        ell('shoe-upper-'+side,(x,.105,.012),(.058,.025,.061),white,'foot.'+side)
        for k in range(3):curve('lace-'+side+str(k),[(x-.033,.116-k*.006,.028+k*.022),(x,.121-k*.006,.028+k*.022),(x+.033,.116-k*.006,.028+k*.022)],.0032,cream,'foot.'+side)
        ax=sign*.213
        loft('sleeve-'+side,[(ax,.52,0,.048,.052),(ax,.55,0,.054,.056),(ax,.70,0,.057,.063),(ax,.79,0,.066,.072),(ax,.93,0,.077,.077),(ax,.98,0,.044,.050)],outfit,weights=joint('upper_arm.'+side,'forearm.'+side,.745))
        loft('cuff-'+side,[(ax,.53,0,.052,.054),(ax,.56,0,.054,.056),(ax,.58,0,.055,.056)],outfit,'forearm.'+side)
        for k in range(3):
            h=.61+k*.09
            curve('sleeve-fold-'+side+str(k),[(ax-.035,h,.048),(ax,h-.015,.062),(ax+.035,h+.008,.048)],.0028,outfit,'forearm.'+side if h<.74 else 'upper_arm.'+side)
        ell('palm-'+side,(ax,.475,.012),(.041,.062,.030),skin,'hand.'+side)
        ell('thumb-'+side,(ax-sign*.036,.490,.026),(.017,.032,.018),skin,'hand.'+side)
        for k in range(3):curve('finger-groove-'+side+str(k),[(ax-.018+k*.014,.44,.035),(ax-.018+k*.014,.467,.041)],.0015,blush,'hand.'+side)
    ell('nose',(0,1.220,.204),(.027,.031,.035),skin)
    curve('smile',[(-.046,1.158,.183),(0,1.143,.199),(.046,1.158,.183)],.0045,mat('lip','#b57168'))
    ell('lower-lip',(0,1.134,.187),(.027,.006,.008),blush)
    if ri<2:
        # Open cardigan panels follow the torso rather than box-shaped blocks.
        for s in [-1,1]:
            loft('cardigan-panel',[(s*.114,.59,.043,.061,.092),(s*.124,.63,.047,.062,.094),(s*.128,.82,.037,.062,.097),(s*.124,.965,.025,.070,.087),(s*.091,.994,.028,.026,.067)],outfit,'spine')
            curve('cardigan-edge',[(s*.07,.60,.139),(s*.067,.78,.153),(s*.073,.94,.132),(s*.052,.99,.101)],.006,outfit,'spine')
            ell('pocket',(s*.13,.686,.128),(.044,.046,.012),outfit,'spine')
            curve('pocket-rim',[(s*.13-.039,.719,.137),(s*.13,.715,.142),(s*.13+.039,.719,.137)],.003,cream,'spine')
        for h in [.64,.73,.82]:ell('button',(.073,h,.147),(.006,.006,.004),sole,'spine',12)
        if False:
            ell('backpack',(0,.78,-.146),(.139,.163,.049),cream,'spine')
            ell('backpack-pocket',(0,.72,-.194),(.095,.065,.017),sole,'spine')
            for s in [-1,1]:curve('bag-strap',[(s*.13,.68,.139),(s*.16,.88,.118),(s*.13,.996,.005),(s*.12,.86,-.189)],.010,sole,'spine')
    else:
        for s in [-1,1]:curve('v-neck',[(s*.072,.988,.081),(s*.055,.957,.115),(0,.907,.127)],.009,cream,'spine')
        ell('chest-pocket',(-.10,.797,.113),(.043,.043,.014),outfit,'spine')
        ell('badge',(.105,.835,.124),(.028,.038,.006),cream,'spine')
        curve('badge-clip',[(.105,.864,.133),(.105,.881,.128)],.006,metal,'spine')
        curve('badge-label',[(.087,.835,.132),(.124,.835,.132)],.003,outfit,'spine')
        if ri==2:
            curve('stethoscope',[(-.071,.993,.089),(-.123,.906,.155),(-.095,.767,.157),(.077,.759,.161),(.102,.910,.144),(.065,.993,.089)],.009,ink,'spine')
            ell('stethoscope-bell',(.078,.759,.174),(.025,.025,.008),metal,'spine')
    # Film character identifiers remain true 3D geometry on the shared skeleton.
    if ri<2:
        ell('hood-back',(0,.985,-.115),(.162,.084,.095),outfit,'spine')
        for sign in [-1,1]:curve('hood-drawstring',[(sign*.07,.978,.12),(sign*.082,.88,.16),(sign*.078,.83,.162)],.004,outfit,'spine')
    if ri in (2,4):
        undershirt=mat('undershirt','#b9d7e1' if ri==2 else '#30384b')
        ell('shirt-inset',(0,.935,.12),(.066,.066,.016),undershirt,'spine')
        for sign in [-1,1]:
            loft('white-coat-panel',[(sign*.104,.44,.025,.075,.102),(sign*.112,.60,.035,.079,.102),(sign*.122,.81,.033,.078,.103),(sign*.114,.97,.016,.075,.095)],outfit,'spine')
            curve('coat-lapel',[(sign*.073,.99,.103),(sign*.128,.906,.145),(sign*.072,.861,.15),(sign*.052,.925,.147)],.012,outfit,'spine')
            ell('coat-pocket',(sign*.12,.635,.137),(.044,.047,.009),outfit,'spine')
        if ri==2:
            tie=mat('tie','#2c3546');loft('tie',[(0,.802,.143,.016,.005),(0,.827,.148,.025,.005),(0,.946,.145,.012,.005)],tie,'spine')
        glasses=mat('glasses','#24292c' if ri==2 else '#8e9397',.28)
        for sign in [-1,1]:
            x=sign*.09
            curve('spectacle-rim',[(x-.069,1.302,.237),(x+.068,1.302,.237),(x+.064,1.222,.237),(x-.062,1.222,.237),(x-.069,1.302,.237)],.004,glasses)
            curve('spectacle-arm',[(sign*.16,1.289,.231),(sign*.227,1.286,.085),(sign*.231,1.26,-.01)],.004,glasses)
        curve('spectacle-bridge',[(-.021,1.279,.24),(0,1.287,.247),(.021,1.279,.24)],.004,glasses)
    if ri==3:
        ell('nurse-watch',(-.105,.891,.135),(.018,.023,.006),metal,'spine')
        ell('watch-face',(-.105,.891,.142),(.014,.018,.004),white,'spine')
    # Pink ribbon is raised, visible from oblique angles.
    curve('hope-ribbon',[(-.119,.872,.156),(-.087,.914,.151),(-.098,.934,.149),(-.112,.917,.152),(-.078,.872,.157)],.005,rose,'spine')
    # Interchangeable complete headwear. Each category is separately selectable at runtime.
    category='scarf'
    ell('scarf-back',(0,1.300,-.059),(.242,.254,.183),scarf)
    ell('scarf-crown',(0,1.36,-.023),(.244,.204,.205),scarf)
    for k in range(3):curve('scarf-fold',[(-.231,1.325+k*.020,.041),(-.12,1.374+k*.022,.173),(.080,1.401+k*.022,.181),(.224,1.351+k*.022,.060)],.004,scarf)
    ell('scarf-knot',(-.169,1.166,-.167),(.066,.071,.047),scarf)
    ell('scarf-tail',(-.167,1.045,-.155),(.044,.132,.029),scarf)
    for k in range(6):
        curve('scarf-tail-fold'+str(k),[(-.193+k*.009,1.15,-.129),(-.187+k*.009,1.04,-.127),(-.181+k*.009,.96,-.14)],.002,scarf)
    category='short'
    ell('hair-cap',(0,1.365,-.049),(.236,.199,.175),hair)
    for k in range(10):
        x=-.18+k*.04;ell('swept-lock',(x,1.418+math.sin(k*.7)*.028,.110),(.074,.078,.085),hair)
        curve('hair-ridge',[(x-.03,1.392,.178),(x+.015,1.446,.166),(x+.03,1.478,.121)],.0035,hair)
    for s in [-1,1]:ell('sideburn',(s*.21,1.292,-.005),(.029,.080,.061),hair)
    category='bob'
    ell('bob-cap',(0,1.355,-.056),(.240,.204,.184),hair)
    for s in [-1,1]:
        ell('bob-side',(s*.197,1.224,-.033),(.063,.176,.115),hair)
        for j in range(3):curve('bob-lock',[(s*(.204+j*.012),1.365,.038),(s*(.228+j*.008),1.212,.052),(s*(.190+j*.014),1.085,.034)],.004,hair)
    for k in range(5):ell('bob-fringe',(-.165+k*.073,1.428-math.sin(k*.8)*.038,.137),(.071,.064,.071),hair)
    category='ponytail'
    ell('tied-hair-cap',(0,1.355,-.056),(.240,.204,.184),hair)
    ell('ponytail',(0,1.14,-.238),(.066,.205,.059),hair)
    ell('hair-tie',(0,1.315,-.227),(.048,.025,.025),ink)
    for sign in [-1,1]:
        curve('side-fringe',[(sign*.05,1.49,.07),(sign*.18,1.39,.15),(sign*.222,1.21,.04)],.019,hair)
        curve('loose-side-lock',[(sign*.21,1.33,.055),(sign*.235,1.19,.025),(sign*.214,1.09,.015)],.006,hair)
    category='cap'
    ell('surgical-cap',(0,1.397,-.033),(.241,.170,.205),outfit)
    curve('cap-edge',[(-.232,1.33,.02),(-.15,1.35,.160),(0,1.36,.184),(.15,1.35,.160),(.232,1.33,.02)],.009,cream)
    ell('cap-knot',(0,1.272,-.230),(.047,.03,.025),outfit)
    category='mask'
    ell('mask',(0,1.170,.188),(.125,.068,.031),mat('mask','#b5d6cc'))
    for h in [1.148,1.169,1.190]:curve('mask-pleat',[(-.093,h,.210),(0,h-.004,.222),(.093,h,.210)],.0025,cream)
    for s in [-1,1]:curve('mask-loop',[(s*.113,1.20,.203),(s*.239,1.245,.025),(s*.115,1.135,.194)],.003,cream)
    # Shared 18-bone armature. Join by semantic part to share materials and keep headwear editable.
    bpy.ops.object.select_all(action='DESELECT');bpy.ops.object.armature_add(enter_editmode=True)
    rig=bpy.context.object;rig.name='HopeCastRig';eb=rig.data.edit_bones;eb.remove(eb[0])
    def bone(name,h,t,parent=None):
        b=eb.new(name);b.head=xyz(h);b.tail=xyz(t)
        if parent:b.parent=eb[parent]
    bone('root',(0,0,0),(0,.12,0));bone('hips',(0,.55,0),(0,.70,0),'root');bone('spine',(0,.70,0),(0,1.0,0),'hips');bone('head',(0,1.0,0),(0,1.47,0),'spine')
    for s,side in [(-1,'L'),(1,'R')]:
        bone('thigh.'+side,(s*.092,.55,0),(s*.092,.32,0),'hips');bone('shin.'+side,(s*.092,.32,0),(s*.092,.09,0),'thigh.'+side);bone('foot.'+side,(s*.092,.09,0),(s*.092,.09,.12),'shin.'+side)
        bone('upper_arm.'+side,(s*.213,.96,0),(s*.213,.745,0),'spine');bone('forearm.'+side,(s*.213,.745,0),(s*.213,.53,0),'upper_arm.'+side);bone('hand.'+side,(s*.213,.53,0),(s*.213,.45,0),'forearm.'+side)
        bone('eye.'+side,(s*.086,1.267,.184),(s*.086,1.32,.184),'head')
    bpy.ops.object.mode_set(mode='OBJECT')
    for cat in ['body','scarf','short','bob','ponytail','cap','mask']:
        objs=[o for o,c in parts if c==cat];bpy.ops.object.select_all(action='DESELECT')
        for o in objs:o.select_set(True)
        bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name='cast_'+cat;o.parent=rig
        mod=o.modifiers.new('Shared smooth skeleton','ARMATURE');mod.object=rig
    # Eight shared actions, authored at 24 fps; runtime adjusts gait to measured distance.
    bpy.context.scene.render.fps=24;rig.animation_data_create()
    animated=['hips','spine','head']+[n+'.'+s for s in ['L','R'] for n in ['thigh','shin','foot','upper_arm','forearm']]
    for action_name,length in [('idle',72),('walk',24),('wave',60),('read',72),('talk',96),('nod',48),('stretch',96),('wish',96)]:
        a=bpy.data.actions.new(action_name);a.use_frame_range=True;a.frame_start=1;a.frame_end=length+1;rig.animation_data.action=a
        for f in range(1,length+2,3):
            t=(f-1)/length*math.tau
            for n in animated:
                b=rig.pose.bones[n];b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0)
            if action_name=='walk':
                rig.pose.bones['hips'].location.y=.008*(1-math.cos(t*2));rig.pose.bones['spine'].rotation_euler.y=.025*math.sin(t)
                for s,phase in [('L',0),('R',math.pi)]:
                    stride=math.sin(t+phase)
                    rig.pose.bones['thigh.'+s].rotation_euler.x=-.34*stride
                    rig.pose.bones['shin.'+s].rotation_euler.x=.53*max(0,-stride)
                    rig.pose.bones['foot.'+s].rotation_euler.x=-.14*max(0,stride)
                    rig.pose.bones['upper_arm.'+s].rotation_euler.x=.25*stride
                    rig.pose.bones['forearm.'+s].rotation_euler.x=-.10-.06*max(0,stride)
            else:
                rig.pose.bones['spine'].rotation_euler.x=.012*math.sin(t)
                rig.pose.bones['head'].rotation_euler.z=.018*math.sin(t)
                for s in ['L','R']:rig.pose.bones['forearm.'+s].rotation_euler.x=-.08
                if action_name=='wave':
                    ease=math.sin(math.pi*(f-1)/length)**.5
                    rig.pose.bones['upper_arm.R'].rotation_euler.z=-1.6*ease
                    rig.pose.bones['forearm.R'].rotation_euler.z=(-.4+.22*math.sin(t*3))*ease
                if action_name=='read':
                    rig.pose.bones['head'].rotation_euler.x=.15
                    for s in ['L','R']:rig.pose.bones['forearm.'+s].rotation_euler.x=-.72
                if action_name=='talk':
                    rig.pose.bones['head'].rotation_euler.x=.04*math.sin(t*2)
                    rig.pose.bones['upper_arm.R'].rotation_euler.x=-.22-.10*math.sin(t)
                    rig.pose.bones['forearm.R'].rotation_euler.x=-.7-.16*math.sin(t*2)
                if action_name=='nod':
                    rig.pose.bones['head'].rotation_euler.x=.12+.10*math.sin(t*2)
                if action_name=='stretch':
                    rig.pose.bones['head'].rotation_euler.z=.08*math.sin(t)
                    for side,sign in [('L',1),('R',-1)]:
                        rig.pose.bones['upper_arm.'+side].rotation_euler.z=sign*(.3+.2*math.sin(t))
                        rig.pose.bones['forearm.'+side].rotation_euler.x=-.25
                if action_name=='wish':
                    rig.pose.bones['head'].rotation_euler.x=-.18
                    for side in ['L','R']:rig.pose.bones['forearm.'+side].rotation_euler.x=-1.15
            for n in animated:
                b=rig.pose.bones[n];b.keyframe_insert('rotation_euler',frame=f);b.keyframe_insert('location',frame=f)
        a.use_fake_user=True
    rig.animation_data.action=None
    for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
    bpy.context.scene.frame_set(1)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(OUT/(role+'.glb')),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_skins=True,export_def_bones=False,export_leaf_bone=False)
    triangles=sum(len(o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH')
    metrics.append({'role':role,'polygons':triangles,'bytes':(OUT/(role+'.glb')).stat().st_size,'actions':['idle','walk','wave','read','talk','nod','stretch','wish']})
    if ri==0:bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).parent/'refined-cast-v06.blend'))
(OUT/'manifest.json').write_text(json.dumps({'version':'v06','authoring':'Blender; editable geometry and shared weighted skeleton','roles':metrics},indent=2))
print('CAST_COMPLETE',json.dumps(metrics))
