#!/usr/bin/env python3
"""
radarSwathGenerator.py
version 1.0
Dominic Filiano
30 July 2025

Generate radar swath polygon from flight transect (KML or MAVLink Waypoints).
Supports simple constant-offset and DEM ray-traced modes.
Beam config: half-beamwidth baked in as 20°.
"""
import argparse
import math
import os
import xml.etree.ElementTree as ET

from shapely.geometry import LineString, Polygon, shape
from shapely.ops import linemerge
import pyproj
import simplekml
import fiona
from fastkml import kml as fastkml_kml
import rasterio
import numpy as np

# baked-in half-beamwidth (degrees)
THETA_HBW = 20.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate radar swath polygon (simple or DEM mode), half-beamwidth=20° baked in")
    parser.add_argument("input",
                        help="Flight path file: .shp, .kml/.kmz, or MAVLink .txt/.waypoints")
    parser.add_argument("--height", "-H", type=float, required=True,
                        help="Flight height AGL (m) at start of line.")
    parser.add_argument("--look-angle", "-a", type=float, required=True,
                        help="Antenna look angle θ (degrees from horizontal).")
    parser.add_argument("--side", choices=["left","right"], default="right",
                        help="Side of flight line to generate swath.")
    parser.add_argument("--dem", metavar="DEM",
                        help="Optional DEM file (GeoTIFF). If omitted, runs simple offset mode.")
    parser.add_argument("--output", "-o", default="swath.kml",
                        help="Output KML file.")
    return parser.parse_args()


def read_flight_path(input_file):
    ext = os.path.splitext(input_file)[1].lower()
    # Shapefile
    if ext == ".shp":
        with fiona.open(input_file) as src:
            for feat in src:
                geom = shape(feat['geometry'])
                if isinstance(geom, LineString):
                    return list(geom.coords)
        raise ValueError("No LineString found in shapefile.")
    # KML/KMZ
    elif ext in [".kml", ".kmz"]:
        data = open(input_file, 'rt', encoding='utf-8').read().encode('utf-8')
        k = fastkml_kml.KML()
        k.from_string(data)
        def recurse_feats(feats):
            for feat in feats:
                geom = getattr(feat, 'geometry', None)
                if geom:
                    try:
                        from shapely.geometry import shape as shp_shape, LineString, MultiLineString
                        geom_shp = shp_shape(geom.geojson())
                        if isinstance(geom_shp, LineString):
                            return list(geom_shp.coords)
                        if isinstance(geom_shp, MultiLineString):
                            merged = linemerge(geom_shp)
                            if isinstance(merged, LineString):
                                return list(merged.coords)
                    except:
                        pass
                nested = getattr(feat, 'features', None)
                if nested:
                    result = recurse_feats(nested)
                    if result:
                        return result
            return None
        coords = recurse_feats(k.features)
        if coords:
            return coords
        # XML fallback
        tree = ET.parse(input_file)
        ns = {'kml':'http://www.opengis.net/kml/2.2'}
        for ls in tree.findall('.//kml:LineString', ns):
            ce = ls.find('kml:coordinates', ns)
            if ce is not None and ce.text:
                parts = ce.text.strip().split()
                coords = [(float(p.split(',')[0]), float(p.split(',')[1])) for p in parts]
                return coords
        raise ValueError("No LineString found in KML/KMZ.")
    # MAVLink Waypoints
    elif ext in [".txt", ".waypoints", ".mission"]:
        coords = []
        with open(input_file) as f:
            for line in f:
                parts = line.strip().split()
                if parts and parts[0].isdigit() and int(parts[0])>0 and len(parts)>=10:
                    lat = float(parts[8])
                    lon = float(parts[9])
                    coords.append((lon, lat))
        if coords:
            return coords
        raise ValueError("No MAVLink waypoints parsed.")
    else:
        raise ValueError(f"Unsupported input extension: {ext}")


def utm_crs_for_lonlat(lon, lat):
    zone = int((lon + 180) / 6) + 1
    south = lat < 0
    return pyproj.CRS(proj='utm', zone=zone, datum='WGS84', south=south)


def densify_line(line, spacing):
    length = line.length
    if length <= 0 or spacing <= 0:
        return line
    num = int(length // spacing)
    dists = [i * spacing for i in range(num + 1)] + [length]
    pts = [line.interpolate(d) for d in sorted(set(dists))]
    return LineString(pts)


def compute_swath(coords, agl, theta, side, dem_path=None):
    # Setup CRS
    crs_geo = pyproj.CRS("EPSG:4326")
    lon0, lat0 = coords[0]
    crs_utm = utm_crs_for_lonlat(lon0, lat0)
    to_utm = pyproj.Transformer.from_crs(crs_geo, crs_utm, always_xy=True).transform
    to_geo = pyproj.Transformer.from_crs(crs_utm, crs_geo, always_xy=True).transform

    # Project flight path
    pts_utm = [to_utm(lon, lat) for lon, lat in coords]

    # Compute beam angles relative to vertical (nadir)
    # theta: look angle from horizontal
    # so central depression from vertical = 90° - theta
    center_vert = 90.0 - theta
    phi_near = math.radians(center_vert - THETA_HBW)
    phi_far  = math.radians(center_vert + THETA_HBW)

    # Simple offset mode
    if dem_path is None:
        l_near = agl * math.tan(phi_near)
        l_far  = agl * math.tan(phi_far)
        seg_normals = []
        for (x0,y0),(x1,y1) in zip(pts_utm, pts_utm[1:]):
            dx,dy=x1-x0,y1-y0; d=math.hypot(dx,dy)
            ux,uy=dx/d,dy/d
            nx,ny=(uy,-ux) if side=='right' else(-uy,ux)
            seg_normals.append((nx,ny))
        vert_normals=[]
        N=len(pts_utm)
        for i in range(N):
            if i==0: vert_normals.append(seg_normals[0])
            elif i==N-1: vert_normals.append(seg_normals[-1])
            else:
                n1=seg_normals[i-1]; n2=seg_normals[i]
                nx,ny=n1[0]+n2[0],n1[1]+n2[1]; m=math.hypot(nx,ny)
                vert_normals.append((nx/m,ny/m))
        near_pts=[(x+nx*l_near, y+ny*l_near) for (x,y),(nx,ny) in zip(pts_utm, vert_normals)]
        far_pts =[ (x+nx*l_far,  y+ny*l_far ) for (x,y),(nx,ny) in zip(pts_utm, vert_normals)]

    # DEM ray-tracing mode
    else:
        dem = rasterio.open(dem_path)
        band = dem.read(1)
        resx,resy = dem.res
        spacing = min(abs(resx), abs(resy))
        base_line = LineString(pts_utm)
        dense_line = densify_line(base_line, spacing)
        pts_utm = list(dense_line.coords)
        idxs = [dem.index(x,y) for x,y in pts_utm]
        elevs = np.array([band[r,c] for r,c in idxs])
        flight_asl = elevs[0] + agl
        agls = flight_asl - elevs
        seg_normals=[]
        for (x0,y0),(x1,y1) in zip(pts_utm, pts_utm[1:]):
            dx,dy=x1-x0,y1-y0; d=math.hypot(dx,dy)
            ux,uy=dx/d,dy/d
            nx,ny=(uy,-ux) if side=='right' else(-uy,ux)
            seg_normals.append((nx,ny))
        vert_normals=[]
        N=len(pts_utm)
        for i in range(N):
            if i==0: vert_normals.append(seg_normals[0])
            elif i==N-1: vert_normals.append(seg_normals[-1])
            else:
                n1=seg_normals[i-1]; n2=seg_normals[i]
                nx,ny=n1[0]+n2[0],n1[1]+n2[1]; m=math.hypot(nx,ny)
                vert_normals.append((nx/m,ny/m))
        def trace_phi(phi):
            def tracer(x,y,nx,ny,h_i,elev0):
                if phi<=0: return (x,y)
                max_flat=h_i*math.tan(phi)
                d=0.0; pd=0.0; pb=h_i; pe=0.0
                while d<=max_flat*1.1:
                    bx,by=x+nx*d,y+ny*d
                    try: r,c=dem.index(bx,by)
                    except: return (x+nx*max_flat,y+ny*max_flat)
                    dem_e=band[r,c]; dem_rel=dem_e-elev0
                    beam_rel=h_i - d/math.tan(phi)
                    if dem_rel>=beam_rel:
                        frac=(pb-pe)/((pb-pe)-(beam_rel-dem_rel))
                        di=pd+frac*(d-pd)
                        return (x+nx*di,y+ny*di)
                    pd,pb,pe=d,beam_rel,dem_rel; d+=spacing
                return (x+nx*max_flat,y+ny*max_flat)
            return tracer
        tn=trace_phi(phi_near); tf=trace_phi(phi_far)
        near_pts=[]; far_pts=[]
        for (x,y),(nx,ny),e0,h0 in zip(pts_utm,vert_normals,elevs,agls):
            near_pts.append(tn(x,y,nx,ny,h0,e0))
            far_pts. append(tf(x,y,nx,ny,h0,e0))

    swath_utm = Polygon(far_pts + near_pts[::-1])
        # Transform UTM polygon back to geographic coordinates
    poly_geo = [to_geo(x, y) for x, y in swath_utm.exterior.coords]
    return poly_geo


def main():
    args = parse_args()
    coords = read_flight_path(args.input)
    poly   = compute_swath(coords, args.height, args.look_angle, args.side, args.dem)
    kml = simplekml.Kml()
    p = kml.newpolygon(name="Radar Swath")
    p.outerboundaryis = poly
    p.style.linestyle.color = simplekml.Color.darkblue
    p.style.linestyle.width = 2
    p.style.polystyle.color = simplekml.Color.changealphaint(100, simplekml.Color.lightblue)
    kml.save(args.output)
    print(f"Saved swath to {args.output}")

if __name__ == "__main__":
    main()