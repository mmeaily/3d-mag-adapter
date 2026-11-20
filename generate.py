"""
Parametric replacement insert generator
========================================

Units: millimetres

Requires:
    CadQuery

Install:
    python -m pip install cadquery

Run:
    python generate.py                 (reads params.json)
    python generate.py other.json      (reads a different parameter file)

Parameters:
    params.json, next to this script.

Output:
    replacement_insert.stl (see "output" in the parameter file)
"""

import json
import math
import sys
from pathlib import Path

import cadquery as cq


# ============================================================
# ASCII MEASUREMENT DIAGRAM
# ============================================================

print(r"""

=============================================================
             INSERT MEASUREMENT REFERENCE
=============================================================


FRONT VIEW
----------

                    <--------- J = 10 mm --------->

                   ┌─────────────────────────────┐
                   │                             │
                   │          TOP BUTTON         │
                   │                             │
                   └─────────────────────────────┘
                   ↑                             ↑
                   │                             │
                   │ K = 4 mm                    │
                   ↓                             │

                   ┌─────────────────────────────┐
                   │                             │
                   │                             │
                   │          MIDDLE             │
                   │          SECTION            │
                   │                             │
                   │              ○              │
                   │             Ø F              │
                   │                             │
                   │                             │
                   └─────────────────────────────┘
                   ↑                             ↑
                   │                             │
                   │ L = 7 mm*                   │
                   ↓                             │

                   ┌─────────────────────────────┐
                   │                             │
                   │        BOTTOM SECTION       │
                   │                             │
                   └─────────────────────────────┘
                   ↑                             ↑
                   │ M = 4 mm                    │
                   ↓                             │


                   <--------- C = 10 mm --------->


                   ↑
                   │
                   │
                   │ B = 15 mm
                   │ OVERALL
                   │ HEIGHT
                   │
                   ↓


HOLE POSITION
-------------

                   TOP
                    ↓

                   ┌───────────────┐
                   │               │
                   │               │
                   │               │
                   │               │
                   │      ○        │
                   │      ↑        │
                   │      │        │
                   │      │        │
                   │      │ E=7.5  │
                   │      │        │
                   │      ↓        │
                   └───────────────┘

                   Hole diameter = F = 6 mm


SIDE VIEW
---------

             <---------- D = 10 mm ---------->

             ┌───────────────────────────────┐
             │          TOP BUTTON            │
             │                                │
             └────────────────────────────────┐
                                              │
                                              │
                                              │
                                              │
                                              │
             ┌────────────────────────────────┘
             │
             │
             │        BOTTOM SECTION
             │
             └───────────────────────────────


HOUSING CURVE
-------------

              <--------- G = 20 mm --------->

                    ╭────────────────╮
                 ╭──╯                ╰──╮
                ╱                        ╲
                ╲________________________╱
                          ↑
                          │
                          │ H = 6 mm
                          │
                          ↓


HOUSING WIDTH
-------------

              <----------- A = 18 mm ----------->

        ┌───────────────────────────────────────────┐
        │                                           │
        │                  INSERT                   │
        │                                           │
        └───────────────────────────────────────────┘


CURRENT MEASUREMENTS
--------------------

Diagram letter / original measurement  ->  params.json name

A = 18 mm    Housing width           ->  HOUSING_WIDTH
B = 15 mm    Insert overall height   ->  INSERT_HEIGHT
C = 10 mm    Insert width            ->  INSERT_WIDTH
D = 10 mm    Insert depth            ->  INSERT_DEPTH
E = 7.5 mm   Hole centre from top    ->  HOLE_FROM_TOP
F =  6 mm    Hole diameter           ->  HOLE_DIAMETER
G = 20 mm    Housing curve width     ->  HOUSING_CURVE_WIDTH
H =  6 mm    Housing curve depth     ->  HOUSING_CURVE_DEPTH
I = 10 mm    Bottom step length      ->  BOTTOM_DEPTH
J = 10 mm    Top button width        ->  TOP_BUTTON_WIDTH
K =  4 mm    Top button height       ->  TOP_BUTTON_HEIGHT
L =  7 mm    Middle section height   ->  MIDDLE_HEIGHT
M =  4 mm    Bottom section height   ->  BOTTOM_HEIGHT


IMPORTANT
---------

The original hand measurements did not add up:

K + L + M = 4 + 8 + 2 = 14 mm

but

B = 15 mm

Photos of the original black part show the bottom band is
about as thick as the top band, so M is taken as 4 mm.  The
script uses B as the authoritative overall height and calculates:

L = B - K - M

L = 15 - 4 - 4
L = 7 mm

The hole is centred in the middle section:

E = K + L / 2 = 4 + 3.5 = 7.5 mm from the top


=============================================================

""")


# ============================================================
# USER PARAMETERS
# ============================================================

# Every parameter lives in params.json (or the file given as the
# first argument), so variants can be tried without editing this
# script.  The names below are the JSON keys; the notes in the JSON
# file explain each one.

PARAMS_FILE = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else Path(__file__).with_name("params.json")
)


def load_params(path):
    """Flatten the JSON groups into {name: value}.

    Groups and keys starting with "_" are notes and are skipped.
    """

    try:

        with open(path, encoding="utf-8") as file:
            groups = json.load(file)

    except FileNotFoundError:

        sys.exit(f"Parameter file not found: {path}")

    except json.JSONDecodeError as error:

        sys.exit(f"{path}: invalid JSON - {error}")

    flat = {}

    for group, values in groups.items():

        if group.startswith("_"):
            continue

        for name, value in values.items():

            if name.startswith("_"):
                continue

            if name in flat:
                sys.exit(f"{path}: '{name}' appears more than once")

            flat[name] = value

    return flat


_params = load_params(PARAMS_FILE)


def param(name):

    try:

        return _params.pop(name)

    except KeyError:

        sys.exit(f"{PARAMS_FILE}: missing parameter '{name}'")


# ------------------------------------------------------------
# Original measured dimensions
# ------------------------------------------------------------

# (The letters are the labels used in the diagram above.)

HOUSING_WIDTH = param("HOUSING_WIDTH")                # A
INSERT_HEIGHT = param("INSERT_HEIGHT")                # B  overall
INSERT_WIDTH = param("INSERT_WIDTH")                  # C
INSERT_DEPTH = param("INSERT_DEPTH")                  # D
HOLE_FROM_TOP = param("HOLE_FROM_TOP")                # E  hole centre
HOLE_DIAMETER = param("HOLE_DIAMETER")                # F
HOUSING_CURVE_WIDTH = param("HOUSING_CURVE_WIDTH")    # G  chord
HOUSING_CURVE_DEPTH = param("HOUSING_CURVE_DEPTH")    # H  sagitta
BOTTOM_DEPTH = param("BOTTOM_DEPTH")                  # I  None follows INSERT_DEPTH
TOP_BUTTON_WIDTH = param("TOP_BUTTON_WIDTH")          # J
TOP_BUTTON_HEIGHT = param("TOP_BUTTON_HEIGHT")        # K
MIDDLE_HEIGHT = param("MIDDLE_HEIGHT")                # L
BOTTOM_HEIGHT = param("BOTTOM_HEIGHT")                # M

# Front-to-back thickness of the middle section (the neck between
# the top button and the bottom section).  The SIDE VIEW shows it
# recessed from the front and flush with the back, but gives no
# dimension for it.
NECK_DEPTH = param("NECK_DEPTH")

HEIGHT_MODE = param("HEIGHT_MODE")


# ------------------------------------------------------------
# Fit / test parameters
# ------------------------------------------------------------

WIDTH_OFFSET = param("WIDTH_OFFSET")
DEPTH_OFFSET = param("DEPTH_OFFSET")
HEIGHT_OFFSET = param("HEIGHT_OFFSET")

HOLE_DIAMETER_OFFSET = param("HOLE_DIAMETER_OFFSET")
HOLE_X_OFFSET = param("HOLE_X_OFFSET")

APPLY_HOUSING_CURVE = param("APPLY_HOUSING_CURVE")
EDGE_RADIUS = param("EDGE_RADIUS")


# ------------------------------------------------------------
# Hollow cylinder (sleeve) that sits in the metal hole
# ------------------------------------------------------------

# A tube that fills the hole, concentric with it, and stands out
# of the back face of the insert so it seats in the metal hole of
# the mag adapter.  Its outer diameter is HOLE_DIAMETER; the wall
# grows inwards, so the hole through the insert shrinks:
#
#     bore diameter = HOLE_DIAMETER - 2 * TUBE_WALL

ADD_TUBE = param("ADD_TUBE")
TUBE_WALL = param("TUBE_WALL")
TUBE_LENGTH = param("TUBE_LENGTH")


# ------------------------------------------------------------
# Curve and output
# ------------------------------------------------------------

CALCULATE_CURVE_FROM_HOUSING = param("CALCULATE_CURVE_FROM_HOUSING")
MANUAL_CURVE_RADIUS = param("MANUAL_CURVE_RADIUS")

OUTPUT_FILE = param("OUTPUT_FILE")
PREVIEW = param("PREVIEW")
PREVIEW_FILE = param("PREVIEW_FILE")


# A typo in a key would otherwise be silently ignored.
if _params:

    sys.exit(
        f"{PARAMS_FILE}: unknown parameter(s): "
        + ", ".join(sorted(_params))
    )

print(f"Parameters: {PARAMS_FILE}")


# ============================================================
# HEIGHT HANDLING
# ============================================================

# "overall":
#
# INSERT_HEIGHT is authoritative.
#
# MIDDLE_HEIGHT is automatically calculated.
#
# INSERT_HEIGHT = TOP_BUTTON_HEIGHT + MIDDLE_HEIGHT + BOTTOM_HEIGHT
#
# 15 = 4 + middle + 4
# middle = 7
#
#
# "sections":
#
# TOP_BUTTON_HEIGHT, MIDDLE_HEIGHT and BOTTOM_HEIGHT are used
# literally.
#
# Overall height is their sum.
#
# (HEIGHT_MODE is set in params.json.)


if HEIGHT_MODE == "overall":

    insert_height = INSERT_HEIGHT

    middle_height = (
        insert_height
        - TOP_BUTTON_HEIGHT
        - BOTTOM_HEIGHT
    )

elif HEIGHT_MODE == "sections":

    middle_height = MIDDLE_HEIGHT

    insert_height = (
        TOP_BUTTON_HEIGHT
        + middle_height
        + BOTTOM_HEIGHT
    )

else:

    raise ValueError(
        "HEIGHT_MODE must be 'overall' or 'sections'"
    )


# ============================================================
# CURVE PARAMETERS
# ============================================================

"""
The housing curve is measured as:

HOUSING_CURVE_WIDTH = 20 mm chord width   (W below)
HOUSING_CURVE_DEPTH =  6 mm sagitta       (H below)

For a circular arc:

                 W²
R = H/2 + -----------
                 8H

equivalently:

R = (W² + 4H²) / (8H)
"""

if CALCULATE_CURVE_FROM_HOUSING:

    CURVE_RADIUS = (
        HOUSING_CURVE_WIDTH ** 2
        + 4.0 * HOUSING_CURVE_DEPTH ** 2
    ) / (8.0 * HOUSING_CURVE_DEPTH)

else:

    CURVE_RADIUS = MANUAL_CURVE_RADIUS


# ============================================================
# DERIVED DIMENSIONS
# ============================================================

width = INSERT_WIDTH + WIDTH_OFFSET
top_width = TOP_BUTTON_WIDTH + WIDTH_OFFSET

depth = INSERT_DEPTH + DEPTH_OFFSET
bottom_depth = (
    INSERT_DEPTH if BOTTOM_DEPTH is None else BOTTOM_DEPTH
) + DEPTH_OFFSET
neck_depth = NECK_DEPTH + DEPTH_OFFSET

height = insert_height + HEIGHT_OFFSET
bottom_height = BOTTOM_HEIGHT

hole_diameter = HOLE_DIAMETER + HOLE_DIAMETER_OFFSET


# Hole measured down from the top.
hole_z = height - HOLE_FROM_TOP

tube_outer_diameter = hole_diameter
bore_diameter = hole_diameter

if ADD_TUBE:

    bore_diameter = tube_outer_diameter - 2.0 * TUBE_WALL

    if bore_diameter <= 0.0:

        raise ValueError(
            f"TUBE_WALL ({TUBE_WALL:.3f} mm) must be less than half "
            f"the hole diameter ({hole_diameter / 2.0:.3f} mm)."
        )


# ============================================================
# PRINT PARAMETERS
# ============================================================

print("=============================================================")
print("PARAMETRIC INSERT")
print("=============================================================")

print(f"Insert width:       {width:.3f} mm")
print(f"Top button width:   {top_width:.3f} mm")
print(f"Insert depth:       {depth:.3f} mm")
print(f"Bottom depth:       {bottom_depth:.3f} mm")
print(f"Neck depth:         {neck_depth:.3f} mm")
print(f"Insert height:      {height:.3f} mm")

print(f"Top button height:  {TOP_BUTTON_HEIGHT:.3f} mm")
print(f"Middle height:      {height - TOP_BUTTON_HEIGHT - BOTTOM_HEIGHT:.3f} mm")
print(f"Bottom height:      {BOTTOM_HEIGHT:.3f} mm")

print(f"Hole diameter:      {hole_diameter:.3f} mm")
print(f"Hole from top:      {HOLE_FROM_TOP:.3f} mm")
print(f"Hole Z position:    {hole_z:.3f} mm")

if ADD_TUBE:
    print(f"Tube outer dia:     {tube_outer_diameter:.3f} mm")
    print(f"Tube wall:          {TUBE_WALL:.3f} mm")
    print(f"Bore diameter:      {bore_diameter:.3f} mm")
    print(f"Tube length:        {TUBE_LENGTH:.3f} mm past the back face")

print(
    f"Housing curve:      {HOUSING_CURVE_WIDTH:.3f} × "
    f"{HOUSING_CURVE_DEPTH:.3f} mm"
)
print(f"Curve radius:       {CURVE_RADIUS:.3f} mm")

print("=============================================================")
print()


# ============================================================
# BUILD SECTIONS
# ============================================================

"""
The insert is three stacked sections (see FRONT VIEW / SIDE VIEW):

    top button      TOP_BUTTON_WIDTH  x  INSERT_DEPTH  x  TOP_BUTTON_HEIGHT
    middle section  INSERT_WIDTH      x  NECK_DEPTH    x  middle height
                                                       (hole, axis Y)
    bottom section  INSERT_WIDTH      x  BOTTOM_DEPTH  x  BOTTOM_HEIGHT

SIDE VIEW (looking from +X, front = -Y on the left):

        ┌──────────┐
        └───────┐  │   top button: full depth
                │  │   middle section: recessed from the front,
                │  │   flush with the back
        ┌───────┘  │
        │          │   bottom section: full depth
        └──────────┘

X = width (centred on 0)
Y = depth (centred on 0, front = -Y, back = +Y)
Z = height (bottom face at 0)
"""


back_y = max(depth, bottom_depth) / 2.0

top_z = height - TOP_BUTTON_HEIGHT
middle_z = bottom_height
middle_height = top_z - middle_z


def section(section_width, section_depth, z0, section_height):
    """Box centred on X, flush with the back face, standing on z0."""

    return (
        cq.Workplane("XY")
        .box(
            section_width,
            section_depth,
            section_height,
            centered=(True, False, False)
        )
        .translate(
            (
                0.0,
                back_y - section_depth,
                z0
            )
        )
    )


bottom_section = section(width, bottom_depth, 0.0, bottom_height)
middle_section = section(width, neck_depth, middle_z, middle_height)
top_button = section(top_width, depth, top_z, TOP_BUTTON_HEIGHT)


# ============================================================
# CURVE THE BACK FACE
# ============================================================

"""
The housing is a concave trough: the arc is seen end-on across the
housing width, i.e. in the Y/Z plane.  The insert is 15 mm tall
across that trough, so its back face is trimmed to the same arc
(radius R, axis along X) and sits flush in the housing.

    SIDE VIEW (front = -Y on the left)

        ┌──────────┐
        └───────┐   ╲     back face curves away
                │    │    from the housing wall
        ┌───────┘   ╱     at the top and bottom
        └──────────┘
"""


R = CURVE_RADIUS

if APPLY_HOUSING_CURVE:

    if R <= height / 2.0:

        raise ValueError(
            f"Curve radius ({R:.3f} mm) must be greater than "
            f"half insert height ({height / 2.0:.3f} mm)."
        )

    # Deepest point of the trough is at mid-height, where the
    # back face stays flush at Y = back_y.
    curve_cutter = (
        cq.Workplane("YZ")
        .center(back_y - R, height / 2.0)
        .circle(R)
        .extrude(
            max(width, top_width) + 2.0,
            both=True
        )
    )

    back_edge_y = (
        back_y
        - R
        + math.sqrt(
            R * R
            - (height / 2.0) ** 2
        )
    )

    print(
        f"Back face at top/bottom edge: Y={back_edge_y:.3f} mm "
        f"({back_y - back_edge_y:.3f} mm shorter than mid-height)"
    )

    if back_edge_y <= back_y - min(depth, bottom_depth):

        raise ValueError(
            "Curve removes the whole top/bottom section "
            "(reduce the curve or increase the depth)."
        )


body = (
    bottom_section
    .union(middle_section)
    .union(top_button)
)

if APPLY_HOUSING_CURVE:

    body = body.intersect(curve_cutter)


# ============================================================
# CREATE HOLE
# ============================================================

"""
Hole runs through the depth of the insert (axis = Y),
visible face-on in the FRONT VIEW.
"""


hole_radius = hole_diameter / 2.0

if hole_z - hole_radius < middle_z or hole_z + hole_radius > top_z:

    print(
        "WARNING: hole extends beyond the middle section "
        f"(hole Z {hole_z - hole_radius:.2f} to "
        f"{hole_z + hole_radius:.2f} mm, "
        f"middle section Z {middle_z:.2f} to {top_z:.2f} mm)."
    )
    print()


hole_reach = back_y * 2.0 + 2.0

if ADD_TUBE:

    """
    Cylinder filling the hole (outer diameter HOLE_DIAMETER),
    standing out of the back face.

    It starts at the front face of the middle section (so nothing
    pokes into the front recess) and ends TUBE_LENGTH past the flat
    back plane.  Because the back face is curved it grows out of
    the curve rather than a flat wall.  It is unioned onto the solid
    body, then the bore (HOLE_DIAMETER - 2 * TUBE_WALL) is cut through
    it below,
    which is what leaves it hollow.
    """

    tube_start_y = back_y - neck_depth
    tube_end_y = back_y + TUBE_LENGTH

    # "XZ" faces -Y, so put the workplane at the far end and
    # extrude back towards the insert.
    tube = (
        cq.Workplane("XZ", origin=(0.0, tube_end_y, 0.0))
        .center(
            HOLE_X_OFFSET,
            hole_z
        )
        .circle(
            tube_outer_diameter / 2.0
        )
        .extrude(
            tube_end_y - tube_start_y
        )
    )

    body = body.union(tube)

    hole_reach = max(hole_reach, tube_end_y + 1.0)


hole = (
    cq.Workplane("XZ")
    .center(
        HOLE_X_OFFSET,
        hole_z
    )
    .circle(
        bore_diameter / 2.0
    )
    .extrude(
        hole_reach,
        both=True
    )
)


# ============================================================
# CUT HOLE
# ============================================================

part = body.cut(hole)


# ============================================================
# OPTIONAL EDGE FILLET
# ============================================================

# Keep at zero initially.
#
# TPU may benefit from rounded edges, but we should establish
# the basic geometry first.  (EDGE_RADIUS is set in params.json.)

if EDGE_RADIUS > 0.0:

    try:

        part = part.edges().fillet(
            EDGE_RADIUS
        )

    except Exception as error:

        print()
        print(
            "WARNING: Edge fillet failed:"
        )

        print(error)


# ============================================================
# EXPORT STL
# ============================================================

cq.exporters.export(
    part,
    OUTPUT_FILE,
    tolerance=0.01,
    angularTolerance=1.0
)


# ============================================================
# PREVIEW IMAGE
# ============================================================

# Renders iso / front / side / back views to a PNG so the shape can
# be reviewed without opening a slicer.  Needs matplotlib
# (python -m pip install matplotlib); skipped if it is missing.
# PREVIEW and PREVIEW_FILE are set in params.json.


def render_preview(solid, filename):

    import numpy as np
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    vertices, triangles = solid.val().tessellate(0.01, 0.1)

    xyz = np.array([(v.x, v.y, v.z) for v in vertices])
    tris = xyz[np.array(triangles)]

    normals = np.cross(
        tris[:, 1] - tris[:, 0],
        tris[:, 2] - tris[:, 0]
    )

    lengths = np.linalg.norm(normals, axis=1)
    normals = normals / np.where(lengths == 0.0, 1.0, lengths)[:, None]

    light = np.array([-0.4, -0.7, 0.6])
    light = light / np.linalg.norm(light)

    shade = 0.35 + 0.65 * np.abs(normals @ light)
    colors = shade[:, None] * np.array([0.62, 0.72, 0.80])

    lo = tris.reshape(-1, 3).min(axis=0)
    hi = tris.reshape(-1, 3).max(axis=0)
    centre = (lo + hi) / 2.0
    half = (hi - lo).max() / 2.0 + 1.0

    views = [
        ("Iso",                       25, -60),
        ("Front (looking along +Y)",   0, -90),
        ("Side (from +X, front left)", 0,   0),
        ("Back (curved face)",         0,  90),
    ]

    fig = plt.figure(figsize=(16, 4.5))

    for index, (title, elevation, azimuth) in enumerate(views):

        ax = fig.add_subplot(1, 4, index + 1, projection="3d")

        ax.add_collection3d(
            Poly3DCollection(
                tris,
                facecolors=colors,
                edgecolors="none"
            )
        )

        ax.set_xlim(centre[0] - half, centre[0] + half)
        ax.set_ylim(centre[1] - half, centre[1] + half)
        ax.set_zlim(centre[2] - half, centre[2] + half)
        ax.set_box_aspect((1, 1, 1))
        ax.set_proj_type("ortho")
        ax.view_init(elev=elevation, azim=azimuth)
        ax.set_axis_off()
        ax.set_title(title, fontsize=10)

    size = hi - lo

    fig.suptitle(
        f"{size[0]:.1f} W x {size[1]:.1f} D x {size[2]:.1f} H mm",
        fontsize=11
    )

    fig.tight_layout()
    fig.savefig(filename, dpi=150)


if PREVIEW:

    try:

        render_preview(part, PREVIEW_FILE)

        print(f"Preview:   {PREVIEW_FILE}")

    except ImportError:

        print("Preview skipped (python -m pip install matplotlib)")

    except Exception as error:

        print(f"WARNING: Preview failed: {error}")


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=============================================================")
print("SUCCESS")
print("=============================================================")

print()
print(
    f"Generated: {OUTPUT_FILE}"
)

print()

print("Final geometry:")
print(
    f"  Width:          {width:.2f} mm"
)

print(
    f"  Depth:          {depth:.2f} mm"
)

print(
    f"  Height:         {height:.2f} mm"
)

print(
    f"  Bore diameter:  {bore_diameter:.2f} mm"
)

print(
    f"  Hole Z:         {hole_z:.2f} mm"
)

if ADD_TUBE:

    print(
        f"  Tube:           {tube_outer_diameter:.2f} mm OD, "
        f"{TUBE_WALL:.2f} mm wall, {TUBE_LENGTH:.2f} mm long"
    )

print(
    f"  Curve radius:   {CURVE_RADIUS:.2f} mm"
)

print()

print(
    "STL ready for slicing."
)

print(
    "============================================================="
)