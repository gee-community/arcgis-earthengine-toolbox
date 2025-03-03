# Copyright 2023 Google LLC
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
