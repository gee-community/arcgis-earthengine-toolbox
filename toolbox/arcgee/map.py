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
import matplotlib.colors as mcolors
import matplotlib.cm as cm


def list_color_ramps() -> list[str]:
    """Return a list all supported color ramps."""
    return [
        "viridis",
        "magma",
        "plasma",
        "cividis",
        "Blues",
        "Greens",
        "Reds",
        "Purples",
        "Oranges",
        "Spectral",
        "turbo",
    ]


def get_color_ramp(name: str, n: int = 10) -> list[str]:
    """Return a list of hex color codes from a matplotlib colormap name."""
    try:
        cmap = cm.get_cmap(name, n)
        return [mcolors.to_hex(cmap(i)) for i in range(cmap.N)]
    except ValueError:
        raise ValueError(f"Colormap '{name}' is not recognized by Matplotlib.")


def add_layer(ee_object, vis_params=None, name=None):

    # Check if Earth Engine object is an Image Collection.
    # If so, then create a mosaic before adding to the map.
    if isinstance(ee_object, ee.ImageCollection):
        ee_object = ee_object.mosaic()

    map_id_dict = ee_object.getMapId(vis_params)

    aprx = arcpy.mp.ArcGISProject("CURRENT")
    m = aprx.listMaps("Map")[0]
    layer = m.addDataFromPath(map_id_dict["tile_fetcher"].url_format)
    if name is not None:
        layer.name = name

    return


# Zoom project map view to point.
def zoom_to_point(aprx, point_coords, extent_coords):
    """Zoom the map view to a point with buffer based on extent.

    Args:
        aprx (ArcGISProject): ArcGIS Pro project object.
        point_coords (list): [lon, lat] coordinates of center point.
        extent_coords (list): List of corner coordinates defining the bounds.
    """
    # Get the current project map view.
    view = aprx.activeView
    # Create an extent around the centroid.
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
    # Assuming the ee object centroid and extent are always in lat/lon.
    extent.spatialReference = arcpy.SpatialReference(4326)

    # Set the map view to the new extent.
    view.camera.setExtent(extent)

    return


# Get map view extent.
def get_map_view_extent(target_epsg=4326):
    """Get the current map view extent coordinates in WGS 84.
    Args:
        target_epsg (int): Target EPSG code for the extent coordinates.
    Returns:
        tuple: (xmin, ymin, xmax, ymax) coordinates in WGS 84.
    """
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    # Get the active map view.
    view = aprx.activeView
    # Get the current camera object, which includes the map view extent.
    camera = view.camera

    # Extract the projection and the boundary coordinates (extent).
    spatial_ref = camera.getExtent().spatialReference
    xmin = camera.getExtent().XMin
    ymin = camera.getExtent().YMin
    xmax = camera.getExtent().XMax
    ymax = camera.getExtent().YMax
    # ArcPro 3.2 uses EPSG 3857 (Web Mercator) as the default projection.
    # Refer to https://epsg.io/3857 for more details.
    # When the user zooms out of the global extent to the blank,
    # the map extent coordinates (values are out of range)
    # can not be converted to ESPG 4326 (latitude and longitude).
    # Need to clip the map extent coordinates to valid EPSG 3857 extent.
    if spatial_ref.PCSCode == 3857:
        arcpy.AddMessage("The current projection is EPSG 3857.")
        xmin, ymin, xmax, ymax = clip_to_epsg3857_extent(xmin, ymin, xmax, ymax)
        arcpy.AddMessage("The map extent has been clipped to valid EPSG 3857 extent.")
    # Check if projection code is the target EPSG code.
    # projected
    poly_prj = spatial_ref.PCSCode
    if poly_prj == 0:
        # geographic
        poly_prj = spatial_ref.GCSCode
    # Always using latitude and longtiude for ee.Geometry, ee will automatically transform.
    if str(poly_prj) not in "EPSG:" + str(target_epsg):
        # Convert the extent corners to target EPSG.
        xmin, ymin = project_to_new_sr(xmin, ymin, spatial_ref, target_epsg)
        xmax, ymax = project_to_new_sr(xmax, ymax, spatial_ref, target_epsg)

    return xmin, ymin, xmax, ymax


# Project a point to a different spatial reference.
def project_to_new_sr(x, y, in_spatial_ref, out_spatial_ref):
    """Project a point from input spatial reference to output spatial reference.

    Args:
        x (float): X coordinate in input spatial reference.
        y (float): Y coordinate in input spatial reference.
        in_spatial_ref (SpatialReference): Input spatial reference object.
        out_spatial_ref (SpatialReference): Output spatial reference object.

    Returns:
        tuple: coordinates in output spatial reference.
    """
    point = arcpy.Point(x, y)
    point_geom = arcpy.PointGeometry(point, in_spatial_ref)
    new_sr = arcpy.SpatialReference(out_spatial_ref)
    point_geom_wgs84 = point_geom.projectAs(new_sr)
    return point_geom_wgs84.centroid.X, point_geom_wgs84.centroid.Y


def clip_to_epsg3857_extent(
    xmin: float, ymin: float, xmax: float, ymax: float
) -> tuple[float, float, float, float]:
    """Clip the extent coordinates to the valid EPSG 3857 extent.

    Args:
        xmin : X coordinate in input spatial reference.
        ymin : Y coordinate in input spatial reference.
        xmax : X coordinate in input spatial reference.
        ymax : Y coordinate in input spatial reference.

    Returns:
        The extent clipped to EPSG 3857's valid extent as (xmin, ymin, xmax, ymax).
    """
    # EPSG 3857 global valid extent in meters.
    MIN_VAL = -20037500
    MAX_VAL = 20037500

    xmin_clipped = max(xmin, MIN_VAL)
    ymin_clipped = max(ymin, MIN_VAL)
    xmax_clipped = min(xmax, MAX_VAL)
    ymax_clipped = min(ymax, MAX_VAL)

    return xmin_clipped, ymin_clipped, xmax_clipped, ymax_clipped
