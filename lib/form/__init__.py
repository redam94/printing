"""form components: organic and decorative geometry (revolved spline bodies, flutes, twists,
wavy sections, blob/cloud outlines) and the mesh branch (noise textures, SDF solids) that the
B-rep kernel cannot do.  Functional components from the other categories still provide every
hole pattern, boss and fit; ``form`` supplies the look.  Mesh-returning components come LAST in a
model's build (nothing in build123d can operate on a mesh afterwards; use ``lib.form.mesh``
booleans if you must)."""
