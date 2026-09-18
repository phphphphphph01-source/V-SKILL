import bpy, math, os
from mathutils import Vector
OUT='/mnt/data/vvv2_edit/static/models/fox.glb'
# clear
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in (bpy.data.materials,):
    pass

def mat(name, hexcol, metallic=0.0, rough=.45):
    h=hexcol.lstrip('#'); c=tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
    m=bpy.data.materials.new(name); m.diffuse_color=(*c,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*c,1); bs.inputs['Roughness'].default_value=rough; bs.inputs['Metallic'].default_value=metallic
    return m
orange=mat('Fox Orange','#F47A28',0,.58); orange2=mat('Fox Light','#FF9A3D',0,.55); white=mat('Warm White','#FFF4E7',0,.68)
navy=mat('V-SKILL Navy','#101A35',.15,.34); blue=mat('V-SKILL Blue','#2678E8',.28,.28); cyan=mat('Tech Cyan','#39DFFF',.45,.22); dark=mat('Goggle Lens','#07111F',.6,.16); pink=mat('Inner Ear','#FFB0A0',0,.62)

def smooth(obj):
    if hasattr(obj.data,'polygons'):
        for p in obj.data.polygons:p.use_smooth=True

def uv(name, loc, scale, material, seg=40, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);smooth(o)
    return o

def ico(name,loc,scale,material,sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);smooth(o);return o

def cone(name,loc,rad,depth,material,scale=(1,1,1),rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=rad,radius2=rad*.10,depth=depth,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);smooth(o);return o

def cube(name,loc,scale,material,bevel=.08,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new('Soft bevel','BEVEL');mod.width=bevel;mod.segments=3
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    return o

def torus(name,loc,major,minor,material,rot=(math.pi/2,0,0),scale=(1,1,1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=48,minor_segments=12,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);smooth(o);return o

# feet and legs
uv('Left Foot',(-.34,.25,.18),(.34,.42,.22),orange2);uv('Right Foot',(.34,.25,.18),(.34,.42,.22),orange2)
uv('Left Leg',(-.34,.48,.02),(.24,.52,.24),orange);uv('Right Leg',(.34,.48,.02),(.24,.52,.24),orange)
# body
uv('Body',(0,1.18,0),(.72,.88,.52),orange)
# explorer vest front, shoulder pieces
uv('Vest Front',(0,1.25,.48),(.48,.60,.11),navy)
cube('Vest V Left',(-.10,1.35,.59),(.045,.20,.025),cyan,.02,rot=(0,.0,-.55));cube('Vest V Right',(.10,1.35,.59),(.045,.20,.025),cyan,.02,rot=(0,.0,.55))
# arms
uv('Left Arm',(-.76,1.18,0),(.22,.58,.22),orange);uv('Right Arm',(.76,1.18,0),(.22,.58,.22),orange)
uv('Left Paw',(-.80,.67,.18),(.25,.24,.28),orange2);uv('Right Paw',(.80,.67,.18),(.25,.24,.28),orange2)
# head
uv('Head',(0,2.55,.02),(1.00,.88,.76),orange)
# muzzle/cheeks
uv('Left Cheek',(-.38,2.38,.60),(.43,.30,.20),white);uv('Right Cheek',(.38,2.38,.60),(.43,.30,.20),white);uv('Muzzle',(0,2.30,.67),(.36,.27,.22),white)
uv('Nose',(0,2.30,.88),(.14,.10,.11),dark)
# eyes + brows
for x in (-.37,.37):
    uv('Eye', (x,2.66,.66),(.16,.21,.10),dark)
    uv('Eye Highlight',(x-.045 if x<0 else x+.045,2.73,.75),(.045,.055,.025),white)
# ears as cones, slightly outward
for x,rzv in [(-.62,-.12),(.62,.12)]:
    cone('Fox Ear',(x,3.42,.0),.44,1.05,orange,scale=(.92,1,.78),rot=(0,rzv,0))
    cone('Inner Ear',(x,3.43,.23),.25,.65,pink,scale=(.8,1,.48),rot=(0,rzv,0))
# tail: 3 connected fluffy lobes behind, tip white
uv('Tail Base',(.67,1.08,-.48),(.42,.60,.48),orange);uv('Tail Curve',(.98,1.48,-.62),(.48,.68,.48),orange2);uv('Tail Tip',(1.02,1.92,-.64),(.40,.48,.40),white)
# goggles: strap and two rims
# strap as torus around head, then front frames
bpy.ops.mesh.primitive_torus_add(major_radius=1.00,minor_radius=.045,major_segments=48,minor_segments=10,location=(0,2.65,.0),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='Goggle Strap';o.scale=(1,.72,1);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(navy);smooth(o)
for x in (-.38,.38):
    torus('Goggle Frame',(x,2.66,.77),.22,.055,blue,rot=(math.pi/2,0,0),scale=(1,1,.8))
    uv('Goggle Lens',(x,2.66,.80),(.18,.18,.045),dark)
cube('Goggle Bridge',(0,2.66,.79),(.14,.035,.035),cyan,.02)
# belt + pouches
torus('Utility Belt',(0,1.12,0),.69,.055,blue,rot=(math.pi/2,0,0),scale=(1,.78,1))
for x in (-.56,.56): cube('Utility Pouch',(x,1.03,.43),(.14,.18,.11),navy,.04)
# badge
cyl=None
bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.10,depth=.035,location=(0,1.95,.56),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='V-SKILL Badge';o.data.materials.append(cyan);smooth(o)
# small backpack hint behind
cube('Backpack',(0,1.40,-.52),(.38,.46,.14),navy,.10)
# ground platform
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=1.55,depth=.08,location=(0,.04,0));o=bpy.context.object;o.name='Holographic Platform';o.data.materials.append(navy)
torus('Platform Rim',(0,.09,0),1.42,.025,cyan,rot=(0,0,0))
# rotate whole model slightly? keep front along +Y? GLB renderer uses +Z as front. Our front is +Z.
# export
bpy.ops.wm.save_as_mainfile(filepath='/mnt/data/vvv2_edit/fox_source.blend')
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB',use_selection=False,export_apply=True)
print('exported',OUT,os.path.getsize(OUT))
