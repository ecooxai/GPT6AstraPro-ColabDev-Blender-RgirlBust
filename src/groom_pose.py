"""Art-directed gravity-aware interpolation for original long-hair meshes.
This is a geometric pose deformation, not a physical hair simulation.
"""
from mathutils import Vector, Matrix

def relax_lower_hair(objects, tilt, turn):
    pivot=Vector((0,0,3.72))
    pose=(Matrix.Translation(pivot)
          @ Matrix.Rotation(turn,4,'Z')
          @ Matrix.Rotation(tilt,4,'Y')
          @ Matrix.Translation(-pivot))
    inverse=pose.inverted()
    changed=0
    for obj in objects:
        if obj.type!='MESH' or not obj.name.startswith('Hair'):
            continue
        world=obj.matrix_world.copy()
        local=world.inverted()
        for vertex in obj.data.vertices:
            point=world@vertex.co
            t=max(0,min(1,(point.z-1.7)/2.6))
            weight=.12+.88*t*t*(3-2*t)
            posed=point.lerp(pose@point,weight)
            vertex.co=local@(inverse@posed)
            changed+=1
        obj.data.update()
    return changed
