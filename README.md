<p align="center"><strong>wpt2kml.py</strong></p>

  - **Description:** Generates a kml from a Mavlinks Waypoint file to help with flight plan visualization.
  - **Version:** 0.1.0
  - **Dependencies:**
      - xml.etree.ElementTree - Element, SubElement, tostring
      - xml.dom.minidom - parseString


<p align="center"><strong>shifty.py</strong></p>

  - **Description:** Shifts radar transect waypoints missions. 1) No vertical offset, along-track shift, 2) No vertical offset, across-track shift, 3) Vertical offset, across-track shift, 4) "Bounce" configuration.
  - **Version:** 0.1.3
  - **Dependencies:**
      - os
      - pyproj
      - math
      - csv


<p align="center"><strong>radarSwathGenerator.py</strong></p>

  - **Description:** Ingests radar flight planning information (AGL, look angle, kml or waypoints file) and generates a kml of the expected radar swath on the ground. Run without a DEM for the 2D "idealized" mode, run with a DEM for a 3D, raytraced version that is terrain aware. If used with a DSM, other obstructions can be considered as well. This script has been packaged into executables that can be run without installing the dependencies. The links are below.
  - **Version:** 1.0
  - **Dependencies:**
      - argparse
      - math
      - os
      - xml.etree.ElementTree
      - Shapely.geometry - LineString, Polygon, shape
      - Shapely.ops - linemerge
      - pyproj
      - simplekml
      - fiona
      - fastkml - kml
      - rasterio
      - numpy
  - **Executables Download links:**
      - Download the executable for [Linux][linux]
      - Download the executable for [Windows][windows]
  - **Running the Executables:**
      - Linux Command Line:
        ```bash
        radarSwathGenerator /path/to/input/file \
          --height [0–120 m] \
          --look-angle [0–90°] \
          --side [right|left] \
          [--dem /path/to/dem.tif] \
          --output /path/to/output.kml
        ```
      - Windows Command Line:
        ```bat
        radarSwathGenerator.exe \path\to\input\file ^
          --height [0–120 m] ^
          --look-angle [0–90°] ^
          --side [right|left] ^
          [--dem /path/to/dem.tif] ^
          --output \path\to\output.kml
        ```

[linux]: https://f005.backblazeb2.com/file/radarSwathGenerator-package-downloads/linux/radarSwathGenerator
[windows]: https://f005.backblazeb2.com/file/radarSwathGenerator-package-downloads/windows/radarSwathGenerator.exe

