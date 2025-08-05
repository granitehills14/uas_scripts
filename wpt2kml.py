# Convert Waypoints Files to KML
# Version 0.1.0
# Last updated: 2025-05-05
# Dominic L. Filiano, with much help from chatGPT
#

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

# File paths
input_path = input("Enter the waypoints file name: ")
output_path = input("Enter the kml file name: ")

# Parse waypoint file
waypoints = []
with open(input_path, 'r') as file:
    lines = file.readlines()

for line in lines[1:]:
    parts = line.strip().split('\t')
    if len(parts) >= 11:
        lat = float(parts[8])
        lon = float(parts[9])
        alt = float(parts[10])
        waypoints.append((lon, lat, alt))

# Create KML structure
kml = Element('kml', xmlns="http://www.opengis.net/kml/2.2")
document = SubElement(kml, 'Document')

# Define a simple dot style using a small circle icon
style = SubElement(document, 'Style', id="dotStyle")
icon_style = SubElement(style, 'IconStyle')
scale = SubElement(icon_style, 'scale')
scale.text = '0.5'
icon = SubElement(icon_style, 'Icon')
href = SubElement(icon, 'href')
href.text = "http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"

# Add placemarks with dot style
for i, (lon, lat, alt) in enumerate(waypoints):
    pm = SubElement(document, 'Placemark')
    name = SubElement(pm, 'name')
    name.text = f"Waypoint {i}"
    style_url = SubElement(pm, 'styleUrl')
    style_url.text = "#dotStyle"
    point = SubElement(pm, 'Point')
    coordinates = SubElement(point, 'coordinates')
    coordinates.text = f"{lon},{lat},{alt}"

# Extract home altitude
homeParts = lines[1].strip().split('\t')
homeAlt = float(homeParts[10]) if len(homeParts) >= 11 else 0.0


# Add LineString using absolute altitude moide
line_pm = SubElement(document, 'Placemark')
name = SubElement(line_pm, 'name')
name.text = "Flight Path"
line_string = SubElement(line_pm, 'LineString')
alt_mode = SubElement(line_string, 'altitudeMode')
alt_mode.text = 'absolute'

tessellate = SubElement(line_string, 'tessellate')
tessellate.text = '1'

line_coords = SubElement(line_string, 'coordinates')
line_coords.text = ' '.join([
    f"{lon},{lat},{alt + homeAlt}" for lon, lat, alt in waypoints[1:]
])

# Format and save
kml_pretty = parseString(tostring(kml)).toprettyxml(indent="  ")
with open(output_path, 'w') as f:
    f.write(kml_pretty)

print(f"KML with dot placemarks and path saved to: {output_path}")