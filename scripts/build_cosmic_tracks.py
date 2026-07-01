#!/usr/bin/env python3
"""
Extract cosmic-ray trajectory polylines from a Geant4 VRML2 export and pack
them into cosmic_tracks.bin for lunar_habitat_vr.html.

Track colors come from the drawByParticleID scheme set in the .mac used to
run the simulation (see LavaTube.mac):
  gamma -> red, e- -> blue, e+ -> brown, mu- -> green, neutron -> magenta,
  proton -> yellow. Anything left unmapped falls back to Geant4's default
  grey.

Binary format (little-endian):
  u32 numTracks
  per track: u16 numPoints, f32x3 color, numPoints * f32x3 point
  Points are in meters, original Geant4 axes (x, y, z) — the viewer applies
  the same axis transform as the main habitat model: (x,y,z) -> (x, z, -y).

Usage: python3 scripts/build_cosmic_tracks.py <input.wrl> <output.bin>
"""
import re
import struct
import sys

SCALE = 0.001  # mm -> m


def parse_tracks(wrl_path):
    with open(wrl_path) as f:
        text = f.read()

    tracks = []
    for block in text.split('#---------- POLYLINE')[1:]:
        cm = re.search(
            r'material Material\s*\{\s*diffuseColor\s+([\-0-9.eE]+)\s+([\-0-9.eE]+)\s+([\-0-9.eE]+)',
            block,
        )
        pm = re.search(r'point\s*\[(.*?)\]', block, re.S)
        if not cm or not pm:
            continue
        r, g, b = (float(x) for x in cm.groups())
        nums = [float(x) for x in re.findall(r'[\-0-9.eE]+', pm.group(1))]
        points = list(zip(nums[0::3], nums[1::3], nums[2::3]))
        if len(points) < 2:
            continue
        tracks.append((r, g, b, points))
    return tracks


def write_bin(tracks, out_path):
    with open(out_path, 'wb') as f:
        f.write(struct.pack('<I', len(tracks)))
        for r, g, b, points in tracks:
            f.write(struct.pack('<H', len(points)))
            f.write(struct.pack('<fff', r, g, b))
            for x, y, z in points:
                f.write(struct.pack('<fff', x * SCALE, y * SCALE, z * SCALE))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    tracks = parse_tracks(sys.argv[1])
    write_bin(tracks, sys.argv[2])
    print(f'Wrote {len(tracks)} tracks to {sys.argv[2]}')
