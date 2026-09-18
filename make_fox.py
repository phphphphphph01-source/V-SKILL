import trimesh, numpy as np, os
from trimesh.transformations import rotation_matrix

OUT='/mnt/data/vskill_work/static/models/fox.glb'
scene=trimesh.Scene()

def mat(name, color, rough=.55, metal=0.0):
    return trimesh.visual.material.PBRMaterial(name=name, baseColorFactor=list(color)+[1], metallicFactor=metal, roughnessFactor=rough)
orange=mat('Fox Orange',(0.93,0.28,0.055),.72)
orange2=mat('Fox Light',(1.0,0.40,0.10),.68)
white=mat('Warm White',(1.0,.96,.90),.78)
dark=mat('Deep Navy',(.025,.055,.11),.38,.15)
blue=mat('V-SKILL Blue',(.08,.48,.95),.30,.25)
cyan=mat('Cyan Tech',(.10,.88,1.0),.25,.35)
black=mat('Goggle Dark',(.015,.025,.045),.18,.55)


def add(mesh, name, material):
    mesh.visual.material=material
    scene.add_geometry(mesh, node_name=name)
    return mesh

def uv(name, radius, scale, pos, material, seg=32, rings=20):
    m=trimesh.creation.uv_sphere(radius=radius, count=[seg,rings])
    m.apply_transform(trimesh.transformations.translation_matrix(pos))
    m.apply_transform(trimesh.transformations.scale_matrix(scale[0])) if False else None
    # nonuniform scale after translation around origin would be wrong; do on vertices directly
    m.vertices *= np.array(scale)
    # translation was before scaling, so fix translation scaled back
    # recreate correctly
    m=trimesh.creation.uv_sphere(radius=radius, count=[seg,rings]); m.vertices*=np.array(scale); m.apply_translation(pos)
    return add(m,name,material)

def box(name, extents, pos, material, rot=None, bevel=0.06):
    m=trimesh.creation.box(extents=extents)
    if bevel:
        # simple rounded impression via subdivision is not reliable; keep clean geometry
        pass
    if rot is not None: m.apply_transform(rot)
    m.apply_translation(pos)
    return add(m,name,material)

def cyl(name, radius, height, pos, material, rot=None):
    m=trimesh.creation.cylinder(radius=radius,height=height,sections=32)
    if rot is not None: m.apply_transform(rot)
    m.apply_translation(pos)
    return add(m,name,material)

def cone(name, r1, r2, height, pos, material, rot=None):
    m=trimesh.creation.cone(radius=r1,height=height,sections=32)
    if rot is not None: m.apply_transform(rot)
    m.apply_translation(pos)
    return add(m,name,material)

def torus(name, major, minor, pos, material, rot=None):
    m=trimesh.creation.torus(major_radius=major,minor_radius=minor,major_sections=48,minor_sections=12)
    if rot is not None:m.apply_transform(rot)
    m.apply_translation(pos)
    return add(m,name,material)

# Grounded feet / legs
uv('Left Foot',.38,(1.0,.62,1.15),(-.43,.48,.18),orange)
uv('Right Foot',.38,(1.0,.62,1.15),(.43,.48,.18),orange)
# compact body
uv('Body',1.0,(.78,1.12,.68),(0,1.55,0),orange)
# white chest patch
uv('White Chest',.92,(.48,.82,.18),(0,1.48,.61),white)
# arms/paws
uv('Left Arm',.48,(.48,1.15,.48),(-.82,1.65,.02),orange)
uv('Right Arm',.48,(.48,1.15,.48),(.82,1.65,.02),orange)
uv('Left Paw',.30,(1.05,.62,1.12),(-.84,.95,.32),orange2)
uv('Right Paw',.30,(1.05,.62,1.12),(.84,.95,.32),orange2)
# large head
uv('Head',1.28,(1.0,.94,.86),(0,3.08,.03),orange)
# cheeks + muzzle, front is +Z
uv('Left White Cheek',.52,(1.15,.78,.30),(-.46,2.84,.70),white)
uv('Right White Cheek',.52,(1.15,.78,.30),(.46,2.84,.70),white)
uv('Muzzle',.46,(1.18,.70,.34),(0,2.74,.78),white)
# nose
uv('Nose',.16,(1.0,.72,.75),(0,2.74,1.02),dark)
# eyes
for x in (-.43,.43):
    uv(('Left' if x<0 else 'Right')+' Eye',.22,(.72,1.12,.34),(x,3.20,.78),dark)
    uv(('Left' if x<0 else 'Right')+' Eye Highlight',.075,(.75,1.0,.40),(x-.05 if x<0 else x+.05,3.27,.91),white)
# upright fox ears: outer orange + inner dark
for x in (-.72,.72):
    # cone points up
    cone(('Left' if x<0 else 'Right')+' Ear',.50,.07,1.25,(x,4.10,.02),orange)
    cone(('Left' if x<0 else 'Right')+' Ear Inner',.28,.02,.72,(x,4.10,.42),dark)
# fluffy tail behind, curving to side
uv('Tail Base',.62,(1.0,1.0,1.35),(.72,1.42,-.66),orange)
uv('Tail Mid',.66,(.90,1.0,1.45),(1.05,1.95,-.92),orange)
uv('Tail Upper',.58,(.88,.95,1.35),(.98,2.45,-1.02),orange2)
uv('Tail White Tip',.55,(.90,.92,1.05),(.78,2.78,-1.02),white)
# goggles: strap + frame + lenses, physically placed on face
# strap around head (torus around Y)
torus('Explorer Goggle Strap',1.02,.075,(0,3.20,.02),dark,rotation_matrix(np.pi/2,[1,0,0]))
# two blue/cyan frames and dark lenses on front
for x in (-.40,.40):
    torus(('Left' if x<0 else 'Right')+' Goggle Frame',.28,.075,(x,3.22,.82),blue)
    uv(('Left' if x<0 else 'Right')+' Goggle Lens',.23,(1,1,.22),(x,3.22,.87),black)
box('Goggle Bridge',(.18,.10,.12),(0,3.22,.84),cyan,bevel=0)
# small top tech bar
torus('Tech Headband',.98,.035,(0,3.20,.02),cyan,rotation_matrix(np.pi/2,[1,0,0]))
# utility belt around waist
torus('Utility Belt',.79,.075,(0,1.62,0),blue,rotation_matrix(np.pi/2,[1,0,0]))
# belt pouches physically attached
for x in (-.62,.62): box(('Left' if x<0 else 'Right')+' Utility Pouch',(.28,.34,.20),(x,1.55,.38),dark)
# V emblem: two cyan bars angled on chest
r1=rotation_matrix(np.deg2rad(-35),[0,0,1]); r2=rotation_matrix(np.deg2rad(35),[0,0,1])
box('V Emblem Left',(.10,.38,.055),(-.09,1.76,.80),cyan,rot=r1)
box('V Emblem Right',(.10,.38,.055),(.09,1.76,.80),cyan,rot=r2)
# tiny cyan tech badge
cyl('Tech Badge',.10,.05,(0,2.25,.82),cyan,rotation_matrix(np.pi/2,[1,0,0]))

# improve visuals: compute normals and merge close? Keep separate for material boundaries.
scene.metadata={'asset':'V-SKILL Explorer Fox','rarity':'common','species':'fox','version':'2.0'}
scene.export(OUT)
print('wrote',OUT,os.path.getsize(OUT))
