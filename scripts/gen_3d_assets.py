"""Generate the animated 3D SVGs used by README.md for Arpit Yadav (arpit797).

Six real 3D pieces projected mathematically in Python at keyframes and baked into pure SMIL:
    ring-3d    perspective rotation of a torus of interconnected nodes
    mesh-3d    a travelling wave across a wireframe mesh surface
    sphere-3d  a rotating 3D sphere of tech skills
    stack-3d   isometric architecture stack with requests passing through
    fleet-3d   perspective data routes
    voxel-3d   isometric cubes bobbing on a wave
"""

from __future__ import annotations

import math
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

THEMES = {
    "light": {
        "edge": "#94a3b8",
        "node": "#4f46e5",
        "node_alt": "#0ea5e9",
        "alert": "#e11d48",
        "mesh_near": "#4f46e5",
        "mesh_far": "#a5b4fc",
        "text": "#334155",
        "muted": "#94a3b8",
        "slab_top": "#e0e7ff",
        "slab_left": "#a5b4fc",
        "slab_right": "#c7d2fe",
        "slab_line": "#6366f1",
        "cube_top": "#818cf8",
        "cube_left": "#4338ca",
        "cube_right": "#6366f1",
        "ground": "#cbd5e1",
        "route": "#0ea5e9",
    },
    "dark": {
        "edge": "#4c5a72",
        "node": "#a78bfa",
        "node_alt": "#22d3ee",
        "alert": "#fb7185",
        "mesh_near": "#a78bfa",
        "mesh_far": "#3b3168",
        "text": "#cbd5e1",
        "muted": "#64748b",
        "slab_top": "#312e81",
        "slab_left": "#1e1b4b",
        "slab_right": "#272160",
        "slab_line": "#818cf8",
        "cube_top": "#a78bfa",
        "cube_left": "#4c1d95",
        "cube_right": "#6d28d9",
        "ground": "#334155",
        "route": "#22d3ee",
    },
}


def r(value: float) -> str:
    """Round for compact file size."""
    return f"{value:.1f}".rstrip("0").rstrip(".")


def rotate_y(point, angle):
    x, y, z = point
    c, s = math.cos(angle), math.sin(angle)
    return (x * c + z * s, y, -x * s + z * c)


def rotate_x(point, angle):
    x, y, z = point
    c, s = math.cos(angle), math.sin(angle)
    return (x, y * c - z * s, y * s + z * c)


class Camera:
    """Perspective camera with depth calculation."""

    def __init__(self, width, height, distance, depth_span):
        self.width = width
        self.height = height
        self.distance = distance
        self.depth_span = depth_span
        self.seen = []

    def project(self, point):
        x, y, z = point
        factor = self.distance / (self.distance - z)
        depth = max(0.0, min(1.0, (z + self.depth_span) / (2 * self.depth_span)))
        screen = (self.width / 2 + x * factor, self.height / 2 + y * factor)
        self.seen.append(screen)
        return (screen[0], screen[1], depth)

    def note(self, x, y):
        self.seen.append((x, y))

    def check(self, name, margin=2.0):
        xs = [x for x, _ in self.seen]
        ys = [y for _, y in self.seen]
        box = (min(xs), max(xs), min(ys), max(ys))
        if (box[0] < margin or box[1] > self.width - margin
                or box[2] < margin or box[3] > self.height - margin):
            raise SystemExit(
                f"{name}: geometry leaves viewBox (x {box[0]:.0f}..{box[1]:.0f}, "
                f"y {box[2]:.0f}..{box[3]:.0f})"
            )
        return box


def animate(attribute, values, duration):
    return (f'<animate attributeName="{attribute}" values="{values}" '
            f'dur="{duration}s" repeatCount="indefinite"/>')


def series(values):
    return ";".join(r(v) for v in values)


def opacities(values):
    return ";".join(str(v) for v in values)


def isometric(point, width, height, lift=0.0):
    x, y, z = point
    return (width / 2 + (x - z) * math.cos(math.radians(30)),
            height / 2 + (x + z) * math.sin(math.radians(30)) - y - lift)


def fibonacci_sphere(count: int, radius: float):
    points = []
    golden = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(count):
        y = 1 - (i / (count - 1)) * 2
        ring = math.sqrt(max(0.0, 1 - y * y))
        theta = golden * i
        points.append((math.cos(theta) * ring * radius,
                       y * radius,
                       math.sin(theta) * ring * radius))
    return points


def torus_points(count: int, major: float, minor: float):
    golden = math.pi * (3.0 - math.sqrt(5.0))
    points = []
    for i in range(count):
        phi = 2 * math.pi * i / count
        theta = golden * i * 2.0
        radius = major + minor * math.cos(theta)
        points.append((radius * math.cos(phi),
                       minor * math.sin(theta),
                       radius * math.sin(phi)))
    return points


def nearest_edges(points, per_node: int = 2):
    edges = set()
    for i, a in enumerate(points):
        closest = sorted(
            (math.dist(a, b), j) for j, b in enumerate(points) if j != i
        )
        for _, j in closest[:per_node]:
            edges.add((min(i, j), max(i, j)))
    return sorted(edges)


# ----------------------------- 1. Ring -----------------------------
def ring_svg(theme: str, nodes: int = 44, frames: int = 30,
             width: int = 880, height: int = 280, duration: int = 26) -> str:
    colours = THEMES[theme]
    major, minor = 290.0, 40.0
    tilt = math.radians(12)
    camera = Camera(width, height, distance=1800.0, depth_span=major + minor)
    points = torus_points(nodes, major, minor)
    edges = nearest_edges(points)
    alerts = {5, 16, 27, 38}

    projected = [
        [camera.project(rotate_x(rotate_y(p, 2 * math.pi * f / frames), tilt))
         for p in points]
        for f in range(frames + 1)
    ]
    camera.check(f"ring-3d-{theme}")

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="A network ring rotating in 3D">',
        "<defs>",
        f'<radialGradient id="glow-{theme}">'
        f'<stop offset="0%" stop-color="{colours["alert"]}" stop-opacity=".5"/>'
        f'<stop offset="100%" stop-color="{colours["alert"]}" stop-opacity="0"/>'
        "</radialGradient>",
        "</defs>",
        f'<g stroke="{colours["edge"]}" stroke-width="1" fill="none">',
    ]

    for i, j in edges:
        xs1 = [frame[i][0] for frame in projected]
        ys1 = [frame[i][1] for frame in projected]
        xs2 = [frame[j][0] for frame in projected]
        ys2 = [frame[j][1] for frame in projected]
        ops = [round(0.1 + 0.4 * (frame[i][2] + frame[j][2]) / 2, 2)
               for frame in projected]
        out.append(
            f'<line x1="{r(xs1[0])}" y1="{r(ys1[0])}" x2="{r(xs2[0])}" '
            f'y2="{r(ys2[0])}" opacity="{ops[0]}">'
            + animate("x1", series(xs1), duration)
            + animate("y1", series(ys1), duration)
            + animate("x2", series(xs2), duration)
            + animate("y2", series(ys2), duration)
            + animate("opacity", opacities(ops), duration)
            + "</line>"
        )
    out.append("</g>")

    for index in range(nodes):
        xs = [frame[index][0] for frame in projected]
        ys = [frame[index][1] for frame in projected]
        radii = [1.7 + 3.3 * frame[index][2] for frame in projected]
        ops = [round(0.32 + 0.68 * frame[index][2], 2) for frame in projected]
        fill = colours["alert"] if index in alerts else (
            colours["node"] if index % 3 else colours["node_alt"])

        if index in alerts:
            halo = [value * 4.0 for value in radii]
            out.append(
                f'<circle cx="{r(xs[0])}" cy="{r(ys[0])}" r="{r(halo[0])}" '
                f'fill="url(#glow-{theme})">'
                + animate("cx", series(xs), duration)
                + animate("cy", series(ys), duration)
                + animate("r", series(halo), duration)
                + animate("opacity", "1;.2;1", 2.4)
                + "</circle>"
            )

        out.append(
            f'<circle cx="{r(xs[0])}" cy="{r(ys[0])}" r="{r(radii[0])}" '
            f'fill="{fill}" opacity="{ops[0]}">'
            + animate("cx", series(xs), duration)
            + animate("cy", series(ys), duration)
            + animate("r", series(radii), duration)
            + animate("opacity", opacities(ops), duration)
            + "</circle>"
        )

    out.append("</svg>")
    return "".join(out)


# ----------------------------- 2. Mesh -----------------------------
def mesh_svg(theme: str, columns: int = 17, rows: int = 9, frames: int = 24,
             width: int = 880, height: int = 220, duration: int = 14) -> str:
    colours = THEMES[theme]
    span_x, span_z, amplitude = 340.0, 130.0, 30.0
    yaw, pitch = math.radians(0), math.radians(31)
    camera = Camera(width, height, distance=1600.0,
                    depth_span=span_z + amplitude)

    def surface(u: int, v: int, phase: float):
        x = (u / (columns - 1) - 0.5) * 2 * span_x
        z = (v / (rows - 1) - 0.5) * 2 * span_z
        y = (amplitude * math.sin(3.1 * x / span_x + phase)
             * math.cos(1.6 * z / span_z + phase * 0.6))
        return rotate_x(rotate_y((x, -y, z), yaw), pitch)

    grid = [
        [[camera.project(surface(u, v, 2 * math.pi * f / frames))
          for u in range(columns)]
         for v in range(rows)]
        for f in range(frames + 1)
    ]
    camera.check(f"mesh-3d-{theme}")

    def polyline(sequences):
        values = ";".join(
            " ".join(f"{r(x)},{r(y)}" for x, y, _ in seq) for seq in sequences
        )
        first = " ".join(f"{r(x)},{r(y)}" for x, y, _ in sequences[0])
        return (f'<polyline points="{first}">'
                + animate("points", values, duration)
                + "</polyline>")

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Animated 3D wireframe surface">',
        "<defs>",
        f'<linearGradient id="mesh-{theme}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{colours["mesh_far"]}"/>'
        f'<stop offset="100%" stop-color="{colours["mesh_near"]}"/>'
        "</linearGradient>",
        "</defs>",
        f'<g fill="none" stroke="url(#mesh-{theme})" stroke-width="1.1" '
        'stroke-linecap="round" opacity=".9">',
    ]
    for v in range(rows):
        out.append(polyline([grid[f][v] for f in range(frames + 1)]))
    for u in range(columns):
        out.append(polyline([[grid[f][v][u] for v in range(rows)]
                             for f in range(frames + 1)]))
    out.append("</g></svg>")
    return "".join(out)


# ----------------------------- 3. Sphere (Arpit's Skills) -----------------------------
SKILLS = [
    "JavaScript", "React", "Node.js", "Express", "MongoDB", "Mongoose",
    "C++", "Java", "HTML5", "CSS3", "Tailwind", "REST APIs", "Git",
    "GitHub", "DSA", "Redux", "SQL", "Postman", "Vercel", "Render",
]


def sphere_svg(theme: str, frames: int = 30, width: int = 880,
               height: int = 320, duration: int = 30) -> str:
    colours = THEMES[theme]
    radius = 118.0
    camera = Camera(width, height, distance=radius * 4.0, depth_span=radius)
    points = fibonacci_sphere(len(SKILLS), radius)

    projected = [
        [camera.project(rotate_x(rotate_y(p, 2 * math.pi * f / frames),
                                 math.radians(-10)))
         for p in points]
        for f in range(frames + 1)
    ]
    for frame in projected:
        for (x, y, depth), word in zip(frame, SKILLS):
            half = 0.32 * len(word) * (10 + 9 * depth)
            camera.note(x - half, y)
            camera.note(x + half, y)
    camera.check(f"sphere-3d-{theme}")

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="The stack I work with, on a sphere rotating in 3D">',
        '<g font-family="Segoe UI,Helvetica,Arial,sans-serif" '
        f'font-weight="600" text-anchor="middle" fill="{colours["text"]}">',
    ]
    for index, word in enumerate(SKILLS):
        xs = [frame[index][0] for frame in projected]
        ys = [frame[index][1] for frame in projected]
        sizes = [10 + 9 * frame[index][2] for frame in projected]
        ops = [round(0.28 + 0.72 * frame[index][2], 2) for frame in projected]
        out.append(
            f'<text x="{r(xs[0])}" y="{r(ys[0])}" font-size="{r(sizes[0])}" '
            f'opacity="{ops[0]}">{word}'
            + animate("x", series(xs), duration)
            + animate("y", series(ys), duration)
            + animate("font-size", series(sizes), duration)
            + animate("opacity", opacities(ops), duration)
            + "</text>"
        )
    out.append("</g></svg>")
    return "".join(out)


# ----------------------------- 4. Stack (Full Stack MERN) -----------------------------
def stack_svg(theme: str, frames: int = 24, width: int = 880,
              height: int = 432, duration: int = 6) -> str:
    colours = THEMES[theme]
    half_x, half_z, thickness = 145.0, 66.0, 13.0
    layers = [
        ("MongoDB / DB", 0.0),
        ("Node.js / Express", 62.0),
        ("REST API / Auth", 124.0),
        ("React UI / Client", 186.0),
    ]
    centre = layers[-1][1] / 2
    camera = Camera(width, height, distance=1.0, depth_span=1.0)

    def face(points, lift, fill, opacity=1.0):
        flat = [isometric(p, width, height, lift) for p in points]
        for x, y in flat:
            camera.note(x, y)
        pts = " ".join(f"{r(x)},{r(y)}" for x, y in flat)
        return f'<polygon points="{pts}" fill="{fill}" opacity="{opacity}"/>'

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="An isometric stack of full-stack services">',
    ]

    top_face = [(-half_x, 0.0, -half_z), (half_x, 0.0, -half_z),
                (half_x, 0.0, half_z), (-half_x, 0.0, half_z)]
    left_face = [(-half_x, 0.0, half_z), (half_x, 0.0, half_z),
                 (half_x, -thickness, half_z), (-half_x, -thickness, half_z)]
    right_face = [(half_x, 0.0, -half_z), (half_x, 0.0, half_z),
                  (half_x, -thickness, half_z), (half_x, -thickness, -half_z)]

    for label, raw_lift in layers:
        lift = raw_lift - centre
        out.append(face(left_face, lift, colours["slab_left"]))
        out.append(face(right_face, lift, colours["slab_right"]))
        out.append(face(top_face, lift, colours["slab_top"], 0.96))
        edge = [isometric(p, width, height, lift) for p in top_face]
        pts = " ".join(f"{r(x)},{r(y)}" for x, y in edge)
        out.append(f'<polygon points="{pts}" fill="none" '
                   f'stroke="{colours["slab_line"]}" stroke-width="1" '
                   'opacity=".55"/>')
        corner = isometric((-half_x, 0.0, half_z), width, height, lift)
        label_x = corner[0] - 66
        camera.note(label_x - 110, corner[1] + 6)
        out.append(
            f'<line x1="{r(label_x + 8)}" y1="{r(corner[1])}" '
            f'x2="{r(corner[0] - 2)}" y2="{r(corner[1])}" '
            f'stroke="{colours["muted"]}" stroke-width="1" opacity=".6"/>'
            f'<text x="{r(label_x)}" y="{r(corner[1] + 4)}" '
            'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="13" '
            f'font-weight="600" text-anchor="end" fill="{colours["text"]}" '
            f'opacity=".85">{label}</text>'
        )

    lanes = [(-92.0, -32.0), (0.0, 16.0), (88.0, -6.0)]
    top_lift, bottom_lift = layers[-1][1] - centre, layers[0][1] - centre
    for lane, (x, z) in enumerate(lanes):
        xs, ys, ops = [], [], []
        for f in range(frames + 1):
            phase = (f / frames + lane / len(lanes)) % 1.0
            lift = top_lift + (bottom_lift - top_lift) * phase
            px, py = isometric((x, 0.0, z), width, height, lift)
            camera.note(px, py - 12)
            xs.append(px)
            ys.append(py - 9)
            ops.append(round(min(1.0, 3.4 * min(phase, 1 - phase)), 2))
        out.append(
            f'<circle cx="{r(xs[0])}" cy="{r(ys[0])}" r="4.5" '
            f'fill="{colours["route"]}" opacity="{ops[0]}">'
            + animate("cx", series(xs), duration)
            + animate("cy", series(ys), duration)
            + animate("opacity", opacities(ops), duration)
            + "</circle>"
        )

    camera.check(f"stack-3d-{theme}")
    out.append("</svg>")
    return "".join(out)


# ----------------------------- 5. Fleet -----------------------------
ROUTES = [
    [(-320, 118), (-170, 40), (-40, 94), (110, 18), (300, 72)],
    [(-310, -70), (-140, -102), (30, -46), (200, -94), (320, -30)],
    [(-250, 8), (-60, -30), (90, 60), (250, -10)],
]


def resample(path, count):
    spans = [math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)]
    total = sum(spans)
    points = []
    for step in range(count):
        travelled = total * step / count
        for index, span in enumerate(spans):
            if travelled <= span or index == len(spans) - 1:
                ratio = travelled / span if span else 0.0
                ax, az = path[index]
                bx, bz = path[index + 1]
                points.append((ax + (bx - ax) * ratio, az + (bz - az) * ratio))
                break
            travelled -= span
    return points


def fleet_svg(theme: str, frames: int = 36, width: int = 880,
              height: int = 320, duration: int = 16) -> str:
    colours = THEMES[theme]
    camera = Camera(width, height, distance=1400.0, depth_span=320.0)
    pitch = math.radians(24)

    def project_ground(x, z):
        return camera.project(rotate_x((x, 0.0, z), pitch))

    ground_quad = [(-380, -180), (380, -180), (380, 180), (-380, 180)]
    quad_proj = [project_ground(x, z) for x, z in ground_quad]
    pts = " ".join(f"{r(p[0])},{r(p[1])}" for p in quad_proj)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Data traffic moving along routes in 3D">',
        f'<polygon points="{pts}" fill="none" stroke="{colours["ground"]}" '
        'stroke-width="1" opacity=".35"/>',
    ]

    for route in ROUTES:
        pts_route = [project_ground(x, z) for x, z in route]
        pts_str = " ".join(f"{r(p[0])},{r(p[1])}" for p in pts_route)
        out.append(
            f'<polyline points="{pts_str}" fill="none" '
            f'stroke="{colours["route"]}" stroke-width="1.2" opacity=".4"/>'
        )

        samples = resample(route, frames + 1)
        xs, ys, ops, radii = [], [], [], []
        for p in samples:
            scr = project_ground(p[0], p[1])
            xs.append(scr[0])
            ys.append(scr[1])
            radii.append(2.5 + 2.5 * scr[2])
            ops.append(round(0.4 + 0.6 * scr[2], 2))

        out.append(
            f'<circle cx="{r(xs[0])}" cy="{r(ys[0])}" r="{r(radii[0])}" '
            f'fill="{colours["alert"]}" opacity="{ops[0]}">'
            + animate("cx", series(xs), duration)
            + animate("cy", series(ys), duration)
            + animate("r", series(radii), duration)
            + animate("opacity", opacities(ops), duration)
            + "</circle>"
        )

    camera.check(f"fleet-3d-{theme}")
    out.append("</svg>")
    return "".join(out)


# ----------------------------- 6. Voxel -----------------------------
def voxel_svg(theme: str, columns: int = 7, rows: int = 5, frames: int = 24,
              width: int = 880, height: int = 380, duration: int = 12) -> str:
    colours = THEMES[theme]
    size = 22.0
    step_x, step_z = 48.0, 48.0
    camera = Camera(width, height, distance=1.0, depth_span=1.0)

    top = [(0, 0, 0), (size, 0, 0), (size, 0, size), (0, 0, size)]
    left = [(0, 0, size), (size, 0, size), (size, -size, size), (0, -size, size)]
    right = [(size, 0, 0), (size, 0, size), (size, -size, size), (size, -size, 0)]

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Voxel matrix bobbing in 3D">',
    ]

    for r_idx in range(rows):
        for c_idx in range(columns):
            x = (c_idx - columns / 2) * step_x
            z = (r_idx - rows / 2) * step_z

            ys = []
            for f in range(frames + 1):
                phase = 2 * math.pi * f / frames + (c_idx + r_idx) * 0.4
                lift = 18.0 * math.sin(phase)
                ys.append(lift)

            base_pt = isometric((x, 0, z), width, height, 0)
            camera.note(base_pt[0] - size * 2, base_pt[1] - size * 2)
            camera.note(base_pt[0] + size * 2, base_pt[1] + size * 2)

            def make_poly(face_pts, fill):
                flat = [isometric((x + px, 0 + py, z + pz), width, height, 0)
                        for px, py, pz in face_pts]
                pts_str = " ".join(f"{r(px)},{r(py)}" for px, py in flat)
                return f'<polygon points="{pts_str}" fill="{fill}"/>'

            anim_trans = ";".join(f"0,{r(-y)}" for y in ys)
            out.append(
                f'<g transform="translate(0,0)"><animateTransform attributeName="transform" '
                f'type="translate" values="{anim_trans}" dur="{duration}s" repeatCount="indefinite"/>'
                + make_poly(left, colours["cube_left"])
                + make_poly(right, colours["cube_right"])
                + make_poly(top, colours["cube_top"])
                + "</g>"
            )

    camera.check(f"voxel-3d-{theme}")
    out.append("</svg>")
    return "".join(out)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    written = []
    builders = [
        ("ring", ring_svg),
        ("mesh", mesh_svg),
        ("sphere", sphere_svg),
        ("stack", stack_svg),
        ("fleet", fleet_svg),
        ("voxel", voxel_svg),
    ]
    for theme in ("dark", "light"):
        for name, fn in builders:
            p = ASSETS / f"{name}-3d-{theme}.svg"
            p.write_text(fn(theme), encoding="utf-8")
            written.append(p.name)
    print("wrote " + ", ".join(written))


if __name__ == "__main__":
    main()
