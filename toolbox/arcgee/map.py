# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import arcpy
import ee


def list_color_ramp():
    """
    List all supported color ramps.
    """
    return [
        "viridis",
        "magma",
        "plasma",
        "cividis",
        "blues",
        "greens",
        "reds",
        "purples",
        "orange_red",
        "spectral",
        "turbo",
    ]


def get_color_ramp(ramp_name):
    """
    Return a list of hex color codes based on the color ramp name.

    Supported ramps:
        - viridis
        - magma
        - plasma
        - cividis
        - blues
        - greens
        - reds
        - purples
        - orange_red
        - spectral
        - turbo

    Args:
        ramp_name (str): Name of the color ramp (case-insensitive).

    Returns:
        list of str: Hex color codes.
    """
    ramps = {
        "viridis": [
            "#440154",
            "#482777",
            "#3e4989",
            "#31688e",
            "#26828e",
            "#1f9e89",
            "#35b779",
            "#6ece58",
            "#b5de2b",
            "#fde725",
        ],
        "magma": [
            "#000004",
            "#1b0c41",
            "#4f0c6b",
            "#781c6d",
            "#a52c60",
            "#cf4446",
            "#ed6925",
            "#fb9b06",
            "#f7d13d",
            "#fcfdbf",
        ],
        "plasma": [
            "#0d0887",
            "#41049d",
            "#6a00a8",
            "#8f0da4",
            "#b12a90",
            "#cc4778",
            "#e16462",
            "#f1834b",
            "#fca636",
            "#f0f921",
        ],
        "cividis": [
            "#00204c",
            "#133e7f",
            "#1f5d94",
            "#2d7b9e",
            "#3e98a2",
            "#56b3a4",
            "#78cda1",
            "#a3e59a",
            "#d5f891",
            "#ffffe0",
        ],
        "blues": [
            "#f7fbff",
            "#deebf7",
            "#c6dbef",
            "#9ecae1",
            "#6baed6",
            "#4292c6",
            "#2171b5",
            "#08519c",
            "#08306b",
        ],
        "greens": [
            "#f7fcf5",
            "#e5f5e0",
            "#c7e9c0",
            "#a1d99b",
            "#74c476",
            "#41ab5d",
            "#238b45",
            "#006d2c",
            "#00441b",
        ],
        "reds": [
            "#fff5f0",
            "#fee0d2",
            "#fcbba1",
            "#fc9272",
            "#fb6a4a",
            "#ef3b2c",
            "#cb181d",
            "#a50f15",
            "#67000d",
        ],
        "purples": [
            "#fcfbfd",
            "#efedf5",
            "#dadaeb",
            "#bcbddc",
            "#9e9ac8",
            "#807dba",
            "#6a51a3",
            "#54278f",
            "#3f007d",
        ],
        "orange_red": [
            "#fff5eb",
            "#fee6ce",
            "#fdd0a2",
            "#fdae6b",
            "#fd8d3c",
            "#f16913",
            "#d94801",
            "#a63603",
            "#7f2704",
        ],
        "spectral": [
            "#9e0142",
            "#d53e4f",
            "#f46d43",
            "#fdae61",
            "#fee08b",
            "#e6f598",
            "#abdda4",
            "#66c2a5",
            "#3288bd",
            "#5e4fa2",
        ],
        "turbo": [
            "#30123b",
            "#4440a2",
            "#3580c1",
            "#1fb9b2",
            "#55da69",
            "#a5eb2a",
            "#ffe713",
            "#f8a911",
            "#e75a22",
            "#b2112d",
        ],
    }

    ramp_name = ramp_name.strip().lower()
    return ramps.get(ramp_name, [])


def add_layer(ee_object, vis_params=None, name=None):

    # check if Earth Engine object is a ImageCollection
    # if so, then create a mosaic before
    if isinstance(ee_object, ee.ImageCollection):
        ee_object = ee_object.mosaic()

    map_id_dict = ee_object.getMapId(vis_params)

    aprx = arcpy.mp.ArcGISProject("CURRENT")
    m = aprx.listMaps("Map")[0]
    layer = m.addDataFromPath(map_id_dict["tile_fetcher"].url_format)
    if name is not None:
        layer.name = name

    return


# Zoom project map view to point
def zoom_to_point(aprx, point_coords, extent_coords):
    """Zoom the map view to a point with buffer based on extent.

    Args:
        aprx (ArcGISProject): ArcGIS Pro project object
        point_coords (list): [lon, lat] coordinates of center point
        extent_coords (list): List of corner coordinates defining the bounds
    """
    # get current project map view
    view = aprx.activeView
    # Create an extent around the centroid
    centroid_x, centroid_y = point_coords
    bottom_left = extent_coords[0]
    top_right = extent_coords[2]
    x_min = bottom_left[0]
    y_min = bottom_left[1]
    x_max = top_right[0]
    y_max = top_right[1]
    width = x_max - x_min
    height = y_max - y_min
    zoom_buffer = max(width, height) * 0.6

    extent = arcpy.Extent(
        centroid_x - zoom_buffer,  # xmin
        centroid_y - zoom_buffer,  # ymin
        centroid_x + zoom_buffer,  # xmax
        centroid_y + zoom_buffer,  # ymax
    )
    # assuming the ee object centroid and extent are always in lat/lon
    extent.spatialReference = arcpy.SpatialReference(4326)

    # Set the map view to the new extent
    view.camera.setExtent(extent)

    return


# Get map view extent
def get_map_view_extent(target_epsg=4326):
    """Get the current map view extent coordinates in WGS 84.
    Args:
        target_epsg (int): Target EPSG code for the extent coordinates
    Returns:
        tuple: (xmin, ymin, xmax, ymax) coordinates in WGS 84
    """
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    # Get the active map view
    view = aprx.activeView
    # Get the current camera object, which includes the map view extent
    camera = view.camera

    # Extract the projection and the boundary coordinates (extent)
    spatial_ref = camera.getExtent().spatialReference
    xmin = camera.getExtent().XMin
    ymin = camera.getExtent().YMin
    xmax = camera.getExtent().XMax
    ymax = camera.getExtent().YMax
    # ArcPro 3.2 uses EPSG 3857 as default projection
    # When the user zooms out of the global extent, the map extent coordinates can not be converted to ESPG 4326
    # Need to clip the map extent coordinates to EPSG 3857 extent
    if spatial_ref.PCSCode == 3857:
        arcpy.AddMessage("Make sure the current extent is within EPSG 3857 extent ...")
        xmin, ymin, xmax, ymax = clip_to_epsg3857_extent(xmin, ymin, xmax, ymax)
    # Check if projection code is the target EPSG code
    # projected
    poly_prj = spatial_ref.PCSCode
    if poly_prj == 0:
        # geographic
        poly_prj = spatial_ref.GCSCode
    # Always using latitude and longtiude for ee.Geometry, ee will automatically transform
    if str(poly_prj) not in "EPSG:" + str(target_epsg):
        # Convert the extent corners to target EPSG
        xmin, ymin = project_to_new_sr(xmin, ymin, spatial_ref, target_epsg)
        xmax, ymax = project_to_new_sr(xmax, ymax, spatial_ref, target_epsg)

    return xmin, ymin, xmax, ymax


# Project a point to a different spatial reference
def project_to_new_sr(x, y, in_spatial_ref, out_spatial_ref):
    """Project a point from input spatial reference to output spatial reference.

    Args:
        x (float): X coordinate in input spatial reference
        y (float): Y coordinate in input spatial reference
        in_spatial_ref (SpatialReference): Input spatial reference object
        out_spatial_ref (SpatialReference): Output spatial reference object

    Returns:
        tuple: coordinates in output spatial reference
    """
    point = arcpy.Point(x, y)
    point_geom = arcpy.PointGeometry(point, in_spatial_ref)
    new_sr = arcpy.SpatialReference(out_spatial_ref)
    point_geom_wgs84 = point_geom.projectAs(new_sr)
    return point_geom_wgs84.centroid.X, point_geom_wgs84.centroid.Y


def clip_to_epsg3857_extent(xmin, ymin, xmax, ymax):
    # EPSG:3857 global valid extent in meters
    MIN_VAL = -20037500
    MAX_VAL = 20037500

    # Clip each coordinate to the valid range
    xmin_clipped = max(xmin, MIN_VAL)
    ymin_clipped = max(ymin, MIN_VAL)
    xmax_clipped = min(xmax, MAX_VAL)
    ymax_clipped = min(ymax, MAX_VAL)

    return (xmin_clipped, ymin_clipped, xmax_clipped, ymax_clipped)
