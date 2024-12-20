# -*- coding: utf-8 -*-

import arcpy
import ee
import os
import json
import requests
import numpy as np
import xarray

# ArcGEE version
__version__ = "0.0.1"

# import rasterio
# from rasterio.transform import from_origin
from google.cloud import storage

import arcgee

# import logging

# import arcgee.arctools as arctools

# logger = logging.getLogger(__name__)

""" Define functions"""


def init_and_set_tags(project=None, workload_tag=None):
    ee.Initialize(project=project)

    user_agent = f"ArcGIS_EE/{__version__}/ArcPy/{arcpy.__version__}"
    if ee.data.getUserAgent() != user_agent:
        ee.data.setUserAgent(user_agent)

    ee.data.setDefaultWorkloadTag("arcgis-ee-connector")

    if workload_tag is not None:
        ee.data.setWorkloadTag(workload_tag)

    # check initialization setup
    project_id = ee.data.getProjectConfig()["name"].split("/")[1]
    arcpy.AddMessage(f"Current project ID: {project_id}")
    arcpy.AddMessage(f"Current user agent: {ee.data.getUserAgent()}")
    arcpy.AddMessage(f"Current workload tag: {ee.data.getWorkloadTag()}")
    arcpy.AddMessage("Earth Engine is ready to use.")

    return


# Project a point to WGS 84 (EPSG 4326)
def project_to_wgs84(x, y, in_spatial_ref):
    point = arcpy.Point(x, y)
    point_geom = arcpy.PointGeometry(point, in_spatial_ref)
    wgs84 = arcpy.SpatialReference(4326)
    point_geom_wgs84 = point_geom.projectAs(wgs84)
    return point_geom_wgs84.centroid.X, point_geom_wgs84.centroid.Y


# Get centroid and extent coordinates of input image or feature collection
def get_object_centroid(obj, error_margin):
    # get centroid geometry from input image
    centroid = obj.geometry().centroid(error_margin)
    # coordinates in list
    centroid_coords = centroid.coordinates().getInfo()
    # get image extent
    extent = obj.geometry().bounds(error_margin)
    # coordinates in list
    extent_coords = extent.coordinates().get(0).getInfo()
    return centroid_coords, extent_coords


# Zoom project map view to point
def zoom_to_point(aprx, point_coords, extent_coords):
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

    # Set the map view to the new extent
    view.camera.setExtent(extent)

    return


# Get map view extent
def get_map_view_extent():
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
    # Check if projection code is 4326
    # projected
    poly_prj = spatial_ref.PCSCode
    if poly_prj == 0:
        # geographic
        poly_prj = spatial_ref.GCSCode
    # Always using latitude and longtiude for ee.Geometry, ee will automatically transform
    if str(poly_prj) not in "EPSG:4326":
        # Convert the extent corners to EPSG 4326
        xmin, ymin = project_to_wgs84(xmin, ymin, spatial_ref)
        xmax, ymax = project_to_wgs84(xmax, ymax, spatial_ref)

    return xmin, ymin, xmax, ymax


# Get the coordinates from polygon feature layer
def get_polygon_coords(in_poly):
    spatial_ref = arcpy.Describe(in_poly).spatialReference
    poly_prj = spatial_ref.PCSCode
    if poly_prj == 0:
        poly_prj = spatial_ref.GCSCode
    arcpy.AddMessage("Input feature layer projection CRS is " + str(poly_prj))

    # Project input feature to EPSG:4326 if needed
    target_poly = in_poly
    if str(poly_prj) not in "EPSG:4326":
        arcpy.AddMessage("Projecting input feature layer to EPSG:4326 ...")
        out_sr = arcpy.SpatialReference(4326)
        arcpy.Project_management(in_poly, "poly_temp", out_sr)
        target_poly = "poly_temp"

    # convert input feature to geojson
    arcpy.FeaturesToJSON_conversion(
        target_poly, "temp.geojson", "FORMATTED", "", "", "GEOJSON"
    )

    # Read the GeoJSON file
    upper_path = os.path.dirname(arcpy.env.workspace)
    file_geojson = os.path.join(upper_path, "temp.geojson")
    with open(file_geojson) as f:
        geojson_data = json.load(f)

    # Collect polygon object coordinates
    coords = []
    for feature in geojson_data["features"]:
        coords.append(feature["geometry"]["coordinates"])
    arcpy.AddMessage("Total number of polygon objects: " + str(len(coords)))

    # Delete temporary geojson
    if target_poly == "poly_temp":
        arcpy.management.Delete("poly_temp")
    arcpy.management.Delete(file_geojson)

    return coords


# Check whether use projection or crs code for image to xarray dataset
def whether_use_projection(ic):
    # Start with original projection
    prj = ic.first().select(0).projection()
    # Check crs code
    crs_code = prj.crs().getInfo()
    # Three scenarios: EPSG is unknown, EPSG is 4326, EPSG is others
    if (crs_code is None) or (crs_code == "EPSG:4326"):
        use_projection = True
        arcpy.AddMessage("Open dataset with projection")
    # ESPG is others
    # ValueError: cannot convert float NaN to integer will occur if using projection
    else:
        use_projection = False
        arcpy.AddMessage("Open dataset with CRS code")

    return use_projection


# Download GEE Image to GeoTiff
def image_to_geotiff(
    ic,
    bands,
    crs,
    scale_ds,
    roi,
    use_projection,
    out_tiff,
):
    import rasterio
    from rasterio.transform import from_origin

    prj = ic.first().select(0).projection()
    crs_code = prj.crs().getInfo()

    # When EPSG is unknown or 4326, use projection
    if use_projection:
        ds = xarray.open_dataset(
            ic,
            engine="ee",
            projection=prj,
            scale=scale_ds,
            geometry=roi,
        )
        # Use either X/Y or lat/lon depending on the avaialability
        if "X" in list(ds.variables.keys()):
            arcpy.AddMessage("Use X/Y to define tranform")
            transform = from_origin(
                ds["X"].values[0], ds["Y"].values[-1], scale_ds, -scale_ds
            )
        else:
            arcpy.AddMessage("Use lat/lon to define transform")
            scale_x = abs(ds["lon"].values[0] - ds["lon"].values[1])
            scale_y = abs(ds["lat"].values[0] - ds["lat"].values[1])
            transform = from_origin(
                ds["lon"].values[0], ds["lat"].values[-1], scale_x, -scale_y
            )
    # ESPG is others, use crs code
    # ValueError: cannot convert float NaN to integer will occur if using projection
    else:
        ds = xarray.open_dataset(
            ic, engine="ee", crs=crs_code, scale=scale_ds, geometry=roi
        )
        if "X" in list(ds.variables.keys()):
            arcpy.AddMessage("Use X/Y to define tranform")
            transform = from_origin(
                ds["X"].values[0], ds["Y"].values[0], scale_ds, -scale_ds
            )
        else:
            arcpy.AddMessage("Use lat/lon to define transform")
            scale_x = abs(ds["lon"].values[0] - ds["lon"].values[1])
            scale_y = abs(ds["lat"].values[0] - ds["lat"].values[1])
            transform = from_origin(
                ds["lon"].values[0], ds["lat"].values[0], scale_x, -scale_y
            )
    # Display transform parameters
    arcpy.AddMessage(transform)

    meta = {
        "driver": "GTiff",
        "height": ds[bands[0]].shape[2],
        "width": ds[bands[0]].shape[1],
        "count": len(bands),  # Number of bands
        "dtype": ds[bands[0]].dtype,  # Data type of the array
        "crs": crs,  # Coordinate Reference System, change if needed
        "transform": transform,
    }

    # Store band names
    band_names = {}
    i = 1
    for iband in bands:
        band_names["band_" + str(i)] = iband
        i += 1

    # Write the array to a multiband GeoTIFF file
    arcpy.AddMessage("Save image to " + out_tiff + " ...")
    i = 1
    with rasterio.open(out_tiff, "w", **meta) as dst:
        for iband in bands:
            if use_projection:
                dst.write(np.flipud(np.transpose(ds[iband].values[0])), i)
            else:
                dst.write(np.transpose(ds[iband].values[0]), i)

            i += 1
        # write band names into output tiff
        dst.update_tags(**band_names)
    return


# Upload local file to Google Cloud Storage bucket
def upload_to_gcs_bucket(
    storage_client, bucket_name, source_file_name, destination_blob_name
):
    arcpy.AddMessage("Upload to Google Cloud Storage ...")
    """Uploads a file to the bucket."""
    # Get the bucket that the file will be uploaded to
    bucket = storage_client.bucket(bucket_name)

    # Create a new blob and upload the file's content
    blob = bucket.blob(destination_blob_name)

    # Upload the file
    blob.upload_from_filename(source_file_name)

    full_blob_name = bucket_name + "/" + destination_blob_name
    arcpy.AddMessage(f"File {source_file_name} has been uploaded to {full_blob_name}.")


# Convert Google Cloud Storage file to Earth Engine asset
def gcs_file_to_ee_asset(asset_type, asset_id, bucket_uri):
    import subprocess

    arcpy.AddMessage("Convert Google Cloud Storage file to Earth Engine asset ...")
    arcpy.AddMessage("Upload " + bucket_uri + " to " + asset_id)
    # Define the Earth Engine CLI command
    command = [
        "earthengine",
        "upload",
        asset_type,
        "--asset_id=" + asset_id,
        bucket_uri,
    ]

    # Run the command
    process = subprocess.run(
        command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Output the result
    arcpy.AddMessage(process.stdout.decode("utf-8"))


# Create an Earth Engine image collection
def create_image_collection(asset_folder):
    import subprocess

    arcpy.AddMessage("Create an Earth Engine image collection ...")
    # Define the Earth Engine CLI command
    command = [
        "earthengine",
        "create",
        "collection",
        asset_folder,
    ]

    # Run the command
    process = subprocess.run(
        command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Output the result
    arcpy.AddMessage(process.stdout.decode("utf-8"))


# Create a folder on Earth Engine
def create_ee_folder(asset_folder):
    import subprocess

    arcpy.AddMessage("Create an Earth Engine folder ...")
    # Define the Earth Engine CLI command
    command = [
        "earthengine",
        "create",
        "folder",
        asset_folder,
    ]

    # Run the command
    process = subprocess.run(
        command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Output the result
    arcpy.AddMessage(process.stdout.decode("utf-8"))


# Check if an Earth Engine asset already exists
def asset_exists(asset_id):
    try:
        # Try to retrieve asset information
        ee.data.getAsset(asset_id)
        return True
    except ee.EEException:
        # Asset does not exist
        return False


# List all folders in the bucket
def list_folders_recursive(storage_client, bucket_name, prefix=""):
    """Recursively lists all folders in a Google Cloud Storage bucket."""
    # List blobs with a delimiter to group them by "folders"
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix, delimiter="/")

    # Need this code to active blob prefixes, otherwise, blob.prefixes are empty
    for blob in blobs:
        blob_name = blob.name

    folder_list = []
    # Folders are stored in the prefixes attribute
    if blobs.prefixes:
        for folder in blobs.prefixes:
            folder_list.append(folder)
            # Recursively call the function to go deeper into the folder
            folder_list.extend(
                list_folders_recursive(storage_client, bucket_name, prefix=folder)
            )

    return sorted(folder_list)


# List files within a folder in the bucket
def list_files_in_folder(storage_client, bucket_name, folder_name):
    """
    Lists only files within a specified folder in a Google Cloud Storage bucket.

    :param bucket_name: Name of the GCS bucket.
    :param folder_name: Path to the folder within the bucket (e.g., "folder/subfolder/").
    :return: List of file paths within the specified folder.
    """
    blobs = storage_client.list_blobs(bucket_name, prefix=folder_name)
    # for blob in blobs:
    #    blob_name = blob.name

    # Filter out any "folders" (items ending with a trailing slash)
    files = [blob.name for blob in blobs if not blob.name.endswith("/")]

    return files


""" Toolbox """


class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        tools = []

        # authentication tools
        tools.append(GEEInit)
        tools.append(ChangeProjectID)
        tools.append(GEEAuth)

        # data exploration tools
        tools.append(AddImg2MapbyTag)
        tools.append(AddImg2MapbyObj)
        tools.append(AddImgCol2MapbyTag)
        tools.append(AddImgCol2MapbyObj)
        tools.append(AddFeatCol2MapbyTag)
        tools.append(AddFeatCol2MapbyObj)

        # data management tools
        tools.append(DownloadImgbyTag)
        tools.append(DownloadImgbyObj)
        tools.append(DownloadImgColbyTag)
        tools.append(DownloadImgColbyObj)
        tools.append(DownloadImgCol2Gif)
        tools.append(Upload2GCS)
        tools.append(GCSFile2Asset)
        tools.append(SaveAsset2JSON)

        # data processing tools
        tools.append(ApplyFilter)
        tools.append(ApplyMapFunction)
        tools.append(RunPythonScript)
        tools.append(ApplyReducer)
        tools.append(EEOpTool)

        self.tools = tools


""" Authentication Tools """


# Initialize Earth Engine
class GEEInit:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Initialize Earth Engine"
        self.description = ""
        self.category = "Authentication Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="project_id",
            displayName="Specify the Google Cloud project ID for Earth Engine",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="workload_tag",
            displayName="Specify the workload tag",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        params = [param0, param1]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        project_id = parameters[0].valueAsText
        workload_tag = parameters[1].valueAsText

        init_and_set_tags(project_id, workload_tag)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Change Project ID
class ChangeProjectID:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Check or Change Project ID"
        self.description = ""
        self.category = "Authentication Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="current_id",
            displayName="Current project ID is shown below",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param1 = arcpy.Parameter(
            name="current_tag",
            displayName="Current workload tag is shown below",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="new_id",
            displayName="Specify the new project ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="new_tag",
            displayName="Specify the new workload tag",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Fetch the project ID from the credentials
        try:
            project_id = ee.data.getProjectConfig()["name"].split("/")[1]
            parameters[0].value = project_id
        except:
            parameters[0].value = "None"

        # Fetch workload tag
        parameters[1].value = ee.data.getWorkloadTag()

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        new_id = parameters[2].valueAsText
        new_tag = parameters[3].valueAsText

        ee.Initialize(project=new_id)
        project_id = ee.data.getProjectConfig()["name"].split("/")[1]
        arcpy.AddMessage(f"Project ID is now set to {project_id}")
        if new_tag:
            ee.data.setWorkloadTag(new_tag)
            arcpy.AddMessage(f"Workload tag is now set to {ee.data.getWorkloadTag()}")
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# GEE Authentication
class GEEAuth:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Authenticate Earth Engine"
        self.description = ""
        self.category = "Authentication Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="project_id",
            displayName="Specify the Google Cloud project ID for Earth Engine",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param1 = arcpy.Parameter(
            name="workload_tag",
            displayName="Specify the workload tag",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        params = [param0, param1]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Read input parameters
        project_id = parameters[0].valueAsText
        workload_tag = parameters[1].valueAsText

        # Define functions
        def clear_credentials():
            credentials_path = os.path.expanduser("~/.config/earthengine/credentials")
            if os.path.exists(credentials_path):
                os.remove(credentials_path)
                arcpy.AddMessage(
                    "Previous credentials are removed. Re-authenticate now ..."
                )

        def authenticate_earth_engine(project_id):
            try:
                ee.Authenticate()
                init_and_set_tags(project_id, workload_tag)
                arcpy.AddMessage("Authentication successful")
            except Exception as e:
                arcpy.AddMessage(f"Authentication failed: {e}")

        clear_credentials()
        authenticate_earth_engine(project_id)
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


""" Data Exploration Tools """


# Add GEE Image to Map by Asset Tag
class AddImg2MapbyTag:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Image to Map by Asset Tag"
        self.description = ""
        self.category = "Data Exploration Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="asset_tag",
            displayName="Specify the image asset tag",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Specify three bands for RGB visualization",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param3 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="gamma",
            displayName="Specify gamma correction factors",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="out_json",
            displayName="Save the image object to serialized JSON file",
            datatype="DEFile",
            direction="Output",
            parameterType="Optional",
        )

        param6.filter.list = ["json"]

        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Check band list of the selected image
        img_tag = parameters[0].valueAsText
        # Update only when filter list is empty
        if img_tag and not parameters[1].filter.list:
            image = ee.Image(img_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display
            band_res_list = []
            for iband in band_list:
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
            parameters[1].filter.list = band_res_list

        # Reset band filter list when asset tag changes
        if not img_tag:
            parameters[1].filter.list = []

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        img_tag = parameters[0].valueAsText
        band_str = parameters[1].valueAsText
        min_val = parameters[2].valueAsText
        max_val = parameters[3].valueAsText
        gamma_str = parameters[4].valueAsText
        palette_str = parameters[5].valueAsText

        # Define visualization parameters
        vis_params = {}

        # Add bands to vis_params if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            # Ignore the resolution part
            vis_params["bands"] = bands_only

        # Add min and max values if specified
        if min_val:
            vis_params["min"] = float(min_val)
        if max_val:
            vis_params["max"] = float(max_val)

        # Add gamma correction factors if specified
        if gamma_str:
            # Remove ' in gamma string in case users add it
            if "'" in gamma_str:
                gamma_str = gamma_str.replace("'", "")
            gamma = [float(item) for item in gamma_str.split(",")]
            vis_params["gamma"] = gamma

        # Add color palette if specified
        if palette_str:
            # arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str:
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified
            palette = palette_str.split(",")
            # arcpy.AddMessage(palette)
            vis_params["palette"] = palette

        # Get image by label
        img = ee.Image(img_tag)
        # Get the map ID and token
        map_id_dict = img.getMapId(vis_params)

        # Construct the URL
        map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

        # Add map URL to the current ArcMap
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.listMaps("Map")[0]
        tsl = aprxMap.addDataFromPath(map_url)
        # Add band information to map name
        if band_str:
            tsl.name = img_tag + "--" + "--".join(bands_only)
        else:
            tsl.name = img_tag

        # Zoom to image centroid if provided by dataset
        try:
            centroid_coords, bounds_coords = get_object_centroid(img, 1)
            zoom_to_point(aprx, centroid_coords, bounds_coords)
        except:
            pass

        # Save image object to serialized JSON file
        if parameters[6].valueAsText:
            out_json = parameters[6].valueAsText
            if not out_json.endswith(".json"):
                out_json = out_json + ".json"

            arcgee.data.save_ee_result(img, out_json)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Add GEE Image to Map by Serialized Object in JSON
class AddImg2MapbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Image to Map by Serialized Object"
        self.description = ""
        self.category = "Data Exploration Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized image object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param0.filter.list = ["json"]

        param1 = arcpy.Parameter(
            name="current_tag",
            displayName="The asset tag of the selected object is shown below",
            datatype="GPString",
            direction="Input",
            multiValue=False,
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="bands",
            displayName="Specify three bands for RGB visualization",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Optional",
        )

        param3 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="gamma",
            displayName="Specify gamma correction factors",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        json_path = parameters[0].valueAsText
        if json_path:
            # Display the asset tag of the selected object
            image = arcgee.data.load_ee_result(json_path)
            parameters[1].value = image.get("system:id").getInfo()

            # Update when band filter list is empty
            if not parameters[2].filter.list:
                band_names = image.bandNames()
                band_list = band_names.getInfo()
                # Add band resolution information to display
                band_res_list = []
                for iband in band_list:
                    band_tmp = image.select(iband)
                    proj = band_tmp.projection()
                    res = proj.nominalScale().getInfo()
                    band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
                parameters[2].filter.list = band_res_list

        # Reset band filter list when asset tag changes
        if not json_path:
            parameters[1].value = None
            parameters[2].filter.list = []

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        json_path = parameters[0].valueAsText
        band_str = parameters[2].valueAsText
        min_val = parameters[3].valueAsText
        max_val = parameters[4].valueAsText
        gamma_str = parameters[5].valueAsText
        palette_str = parameters[6].valueAsText

        # Define visualization parameters
        vis_params = {}

        # Add bands to vis_params if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            # Ignore the resolution part
            vis_params["bands"] = bands_only

        # Add min and max values if specified
        if min_val:
            vis_params["min"] = float(min_val)
        if max_val:
            vis_params["max"] = float(max_val)

        # Add gamma correction factors if specified
        if gamma_str:
            # Remove ' in gamma string in case users add it
            if "'" in gamma_str:
                gamma_str = gamma_str.replace("'", "")
            gamma = [float(item) for item in gamma_str.split(",")]
            vis_params["gamma"] = gamma

        # Add color palette if specified
        if palette_str:
            # arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str:
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified
            palette = palette_str.split(",")
            # arcpy.AddMessage(palette)
            vis_params["palette"] = palette

        # Get image by label
        img = arcgee.data.load_ee_result(json_path)
        img_tag = img.get("system:id").getInfo()
        # Get the map ID and token
        map_id_dict = img.getMapId(vis_params)

        # Construct the URL
        map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

        # Add map URL to the current ArcMap
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.listMaps("Map")[0]
        tsl = aprxMap.addDataFromPath(map_url)
        # Add band information to map name
        if band_str:
            tsl.name = img_tag + "--" + "--".join(bands_only)
        else:
            tsl.name = img_tag

        # Zoom to image centroid if provided by dataset
        try:
            centroid_coords, bounds_coords = get_object_centroid(img, 1)
            zoom_to_point(aprx, centroid_coords, bounds_coords)
        except:
            pass
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Add GEE Image Collection to Map by Asset Tag
class AddImgCol2MapbyTag:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Image Collection to Map by Asset Tag"
        self.description = ""
        self.category = "Data Exploration Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="asset_tag",
            displayName="Specify the image collection asset tag",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
            multiValue=False,
        )
        param1.columns = [["GPString", "Starting Date"], ["GPString", "Ending Date"]]
        param1.value = [["2014-03-01", "2014-05-01"]]

        param2 = arcpy.Parameter(
            name="filter_bounds",
            displayName="Filter by location in coordinates",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param2.columns = [["GPString", "Longitude"], ["GPString", "Latitude"]]

        param3 = arcpy.Parameter(
            name="use_centroid",
            displayName="Use the center of the current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="image",
            displayName="Select image by image ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param5 = arcpy.Parameter(
            name="bands",
            displayName="Specify three bands for RGB visualization",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param7 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param8 = arcpy.Parameter(
            name="gamma",
            displayName="Specify gamma correction factors",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param9 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param10 = arcpy.Parameter(
            name="out_json",
            displayName="Save the filtered image collection to serialized JSON file",
            datatype="DEFile",
            direction="Output",
            parameterType="Optional",
        )

        param10.filter.list = ["json"]

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
            param7,
            param8,
            param9,
            param10,
        ]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Get the filter dates
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
        else:
            start_date = None
            end_date = None

        # Get the filter bounds
        if parameters[3].value:
            # Disable input coordinates if map extent is used
            parameters[2].enabled = False
            xmin, ymin, xmax, ymax = get_map_view_extent()
            # Get the centroid of map extent
            lon = (xmin + xmax) / 2
            lat = (ymin + ymax) / 2
        else:
            parameters[2].enabled = True
            if parameters[2].valueAsText:
                val_list = parameters[2].values
                lon = val_list[0][0]
                lat = val_list[0][1]
            else:
                lon = None
                lat = None

        # Check image list of a given collection asset
        asset_tag = parameters[0].valueAsText

        # Image collection size could be huge, may take long to load without filters
        # Only retrieve the list of images, when either filter dates or filter bounds are selected
        if asset_tag and ((start_date and end_date) or (lon and lat)):
            collection = ee.ImageCollection(asset_tag)
            # Filter image collection as specified
            if lon is not None and lat is not None:
                collection = collection.filterBounds(
                    ee.Geometry.Point((float(lon), float(lat)))
                )
            if start_date is not None and end_date is not None:
                collection = collection.filterDate(start_date, end_date)
            # Get image IDs from collection
            image_ids = collection.aggregate_array("system:index").getInfo()
            parameters[4].filter.list = image_ids

        # Check band list of the selected image
        img_id = parameters[4].valueAsText
        # Update only when filter list is empty
        if img_id and not parameters[5].filter.list:
            if asset_tag:
                img_tag = asset_tag + "/" + img_id
            else:
                img_tag = img_id
            image = ee.Image(img_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display
            band_res_list = []
            for iband in band_list:
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
            parameters[5].filter.list = band_res_list

        # Reset band filter list when asset tag changes
        if (not img_id) and (not parameters[0].valueAsText):
            parameters[5].filter.list = []

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        asset_tag = parameters[0].valueAsText
        # These three input parameters are only used in updateParameters above
        # filter_dates = parameters[1].valueAsText
        # filter_bounds = parameters[2].valueAsText
        # use_extent = parameters[3].valueAsText
        img_id = parameters[4].valueAsText
        band_str = parameters[5].valueAsText
        min_val = parameters[6].valueAsText
        max_val = parameters[7].valueAsText
        gamma_str = parameters[8].valueAsText
        palette_str = parameters[9].valueAsText

        # Construct asset tag for selected image
        if asset_tag:
            img_tag = asset_tag + "/" + img_id
        else:
            img_tag = img_id

        # Define visualization parameters
        vis_params = {}

        # Add bands to vis_params if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            # Ignore the resolution part
            vis_params["bands"] = bands_only

        # Add min and max values if specified
        if min_val:
            vis_params["min"] = float(min_val)
        if max_val:
            vis_params["max"] = float(max_val)

        # Add gamma correction factors if specified
        if gamma_str:
            # Remove ' in gamma string in case users add it
            if "'" in gamma_str:
                gamma_str = gamma_str.replace("'", "")
            gamma = [float(item) for item in gamma_str.split(",")]
            vis_params["gamma"] = gamma

        # Add color palette if specified
        if palette_str:
            # arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str:
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified
            palette = palette_str.split(",")
            # arcpy.AddMessage(palette)
            vis_params["palette"] = palette

        # Get image by label
        img = ee.Image(img_tag)
        # Get the map ID and token
        map_id_dict = img.getMapId(vis_params)

        # Construct the URL
        map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

        # Add map URL to the current ArcMap
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.listMaps("Map")[0]
        tsl = aprxMap.addDataFromPath(map_url)
        # Add band information to map name
        if band_str:
            tsl.name = img_tag + "--" + "--".join(bands_only)
        else:
            tsl.name = img_tag

        # Zoom to image centroid if provided by dataset
        try:
            centroid_coords, bounds_coords = get_object_centroid(img, 1)
            zoom_to_point(aprx, centroid_coords, bounds_coords)
        except:
            pass

        # Save filtered image collection to serialized JSON file
        if parameters[10].valueAsText:
            out_json = parameters[10].valueAsText
            if not out_json.endswith(".json"):
                out_json = out_json + ".json"

            # Get the filter dates
            if parameters[1].valueAsText:
                val_list = parameters[1].values
                start_date = val_list[0][0]
                end_date = val_list[0][1]
            else:
                start_date = None
                end_date = None

            # Get the filter bounds
            if parameters[3].value:
                # Disable input coordinates if map extent is used
                parameters[2].enabled = False
                xmin, ymin, xmax, ymax = get_map_view_extent()
                # Get the centroid of map extent
                lon = (xmin + xmax) / 2
                lat = (ymin + ymax) / 2
            else:
                parameters[2].enabled = True
                if parameters[2].valueAsText:
                    val_list = parameters[2].values
                    lon = val_list[0][0]
                    lat = val_list[0][1]
                else:
                    lon = None
                    lat = None

            collection = ee.ImageCollection(asset_tag)
            # Filter image collection as specified
            if lon is not None and lat is not None:
                collection = collection.filterBounds(
                    ee.Geometry.Point((float(lon), float(lat)))
                )
            if start_date is not None and end_date is not None:
                collection = collection.filterDate(start_date, end_date)

            arcgee.data.save_ee_result(collection, out_json)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Add GEE Image Collection to Map by Serialized Object in JSON
class AddImgCol2MapbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Image Collection to Map by Serialized Object"
        self.description = ""
        self.category = "Data Exploration Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param0.filter.list = ["json"]

        param1 = arcpy.Parameter(
            name="current_tag",
            displayName="The asset tag of the selected object is shown below",
            datatype="GPString",
            direction="Input",
            multiValue=False,
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="image",
            displayName="Select image by image ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="bands",
            displayName="Specify three bands for RGB visualization",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="gamma",
            displayName="Specify gamma correction factors",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param7 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        params = [param0, param1, param2, param3, param4, param5, param6, param7]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        json_path = parameters[0].valueAsText
        if json_path:
            collection = arcgee.data.load_ee_result(json_path)
            # Display the asset tag of selected object
            parameters[1].value = collection.get("system:id").getInfo()

            # Only fill the image id filter list when it is empty
            if not parameters[2].filter.list:
                # Get image IDs from collection
                image_ids = collection.aggregate_array("system:index").getInfo()
                parameters[2].filter.list = image_ids

            # Check band list of the selected image
            img_id = parameters[2].valueAsText
            # Update only when filter list is empty
            if img_id and not parameters[3].filter.list:
                # retrieve image tag from collection
                asset_tag = collection.get("system:id").getInfo()
                img_tag = asset_tag + "/" + img_id
                image = ee.Image(img_tag)
                band_names = image.bandNames()
                band_list = band_names.getInfo()
                # Add band resolution information to display
                band_res_list = []
                for iband in band_list:
                    band_tmp = image.select(iband)
                    proj = band_tmp.projection()
                    res = proj.nominalScale().getInfo()
                    band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
                parameters[3].filter.list = band_res_list

        # Reset image filter list
        if not json_path:
            parameters[1].value = None
            parameters[2].filter.list = []

        # Reset band filter list when asset tag changes
        if (not parameters[2].valueAsText) and (not json_path):
            parameters[3].filter.list = []

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        json_path = parameters[0].valueAsText
        img_id = parameters[2].valueAsText
        band_str = parameters[3].valueAsText
        min_val = parameters[4].valueAsText
        max_val = parameters[5].valueAsText
        gamma_str = parameters[6].valueAsText
        palette_str = parameters[7].valueAsText

        # load collection object
        collection = arcgee.data.load_ee_result(json_path)
        # Get image tag for layer name
        asset_tag = collection.get("system:id").getInfo()
        img_tag = asset_tag + "/" + img_id
        # Get image by label
        img = ee.Image(img_tag)

        # Define visualization parameters
        vis_params = {}

        # Add bands to vis_params if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            # Ignore the resolution part
            vis_params["bands"] = bands_only

        # Add min and max values if specified
        if min_val:
            vis_params["min"] = float(min_val)
        if max_val:
            vis_params["max"] = float(max_val)

        # Add gamma correction factors if specified
        if gamma_str:
            # Remove ' in gamma string in case users add it
            if "'" in gamma_str:
                gamma_str = gamma_str.replace("'", "")
            gamma = [float(item) for item in gamma_str.split(",")]
            vis_params["gamma"] = gamma

        # Add color palette if specified
        if palette_str:
            # arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str:
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified
            palette = palette_str.split(",")
            # arcpy.AddMessage(palette)
            vis_params["palette"] = palette

        # Get the map ID and token
        map_id_dict = img.getMapId(vis_params)

        # Construct the URL
        map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

        # Add map URL to the current ArcMap
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.listMaps("Map")[0]
        tsl = aprxMap.addDataFromPath(map_url)
        # Add band information to map name
        if band_str:
            tsl.name = img_tag + "--" + "--".join(bands_only)
        else:
            tsl.name = img_tag

        # Zoom to image centroid if provided by dataset
        try:
            centroid_coords, bounds_coords = get_object_centroid(img, 1)
            zoom_to_point(aprx, centroid_coords, bounds_coords)
        except:
            pass

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Add GEE Feature Collection to Map by Asset Tag
class AddFeatCol2MapbyTag:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Feature Collection to Map by Asset Tag"
        self.description = ""
        self.category = "Data Exploration Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """
        Define the tool parameters.

        vis_params = {
            "color": "000000",
            "pointShape": "circle",
            "pointSize": 3,
            "width": 2,
            "lineType": "solid",
            "fillColor": '00FF00',
            "opacity": 0.8,

            "colorOpacity": 1,
            "fillColorOpacity": 0.66,
        }
        """

        param0 = arcpy.Parameter(
            name="asset_tag",
            displayName="Specify the feature collection asset tag",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="filter_props",
            displayName="Filter by Properties",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param1.columns = [
            ["GPString", "Property Name"],
            ["GPString", "Operator"],
            ["GPString", "Filter Value"],
        ]
        param1.filters[1].list = ["==", "!=", ">", ">=", "<", "<="]

        param2 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param2.columns = [["GPString", "Starting Date"], ["GPString", "Ending Date"]]
        # param2.value = [['2014-03-01','2014-05-01']]

        param3 = arcpy.Parameter(
            name="filter_bounds",
            displayName="Filter by location in coordinates",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param3.columns = [["GPString", "Longitude"], ["GPString", "Latitude"]]

        param4 = arcpy.Parameter(
            name="use_centroid",
            displayName="Use the center of the current map view extent (point)",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the current map view extent (area)",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="color",
            displayName="Specify the color for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param7 = arcpy.Parameter(
            name="out_json",
            displayName="Save the filtered feature collection to serialized JSON file",
            datatype="DEFile",
            direction="Output",
            parameterType="Optional",
        )

        param7.filter.list = ["json"]

        # param2 = arcpy.Parameter(
        #     name="point_shape",
        #     displayName="Specify the point shape for visualization",
        #     datatype="GPString",
        #     direction="Input",
        #     parameterType="Optional")
        # param2.filter.list = ['circle','square','diamond','cross','plus','triangle']

        # param3 = arcpy.Parameter(
        #     name="point_size",
        #     displayName="Specify the point size for visualization",
        #     datatype="GPDouble",
        #     direction="Input",
        #     parameterType="Optional")
        # param3.filter.list = [2,4,6,8,10]

        # param4 = arcpy.Parameter(
        #     name="line_width",
        #     displayName="Specify the line width for visualization ",
        #     datatype="GPDouble",
        #     direction="Input",
        #     parameterType="Optional")
        # param4.filter.list = [1,2,3,4,5]

        # param5 = arcpy.Parameter(
        #     name="line_type",
        #     displayName="Specify the line type for visualization",
        #     datatype="GPString",
        #     direction="Input",
        #     parameterType="Optional")
        # param5.filter.list = ['solid','dotted','dashed']

        # param6 = arcpy.Parameter(
        #     name="fill_color",
        #     displayName="Specify the fill color of polygons for visualization",
        #     datatype="GPString",
        #     direction="Input",
        #     parameterType="Optional")

        # param7 = arcpy.Parameter(
        #     name="opacity",
        #     displayName="Specify the opacity for visualization",
        #     datatype="GPDouble",
        #     direction="Input",
        #     parameterType="Optional")
        # # Set the value range
        # param7.filter.type = "Range"
        # param7.filter.list = [0, 1]

        params = [param0, param1, param2, param3, param4, param5, param6, param7]
        # ,param2,param3,param4,param5,param6,param7]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # # Define a function to check the geometry type of a feature.
        # # Filter by geometry type could be computationally expensive
        # def filter_by_geometry_types(feature, geo_types):
        #     # geo_types: List of Polygon, Point, LineString, MultiPolygon, MultiPoint, MultiLineString, GeometryCollection
        #     # Get the geometry of the feature.
        #     geom = feature.geometry()

        #     # Check if the geometry type is 'Polygon'.
        #     return ee.List(geo_types).contains(geom.type())

        if parameters[0].valueAsText and not parameters[1].filters[0].list:
            asset_tag = parameters[0].valueAsText
            fc = ee.FeatureCollection(asset_tag)
            prop_names = fc.first().propertyNames().getInfo()
            parameters[1].filters[0].list = sorted(prop_names)

        # Reset filter list
        if not parameters[0].valueAsText:
            parameters[1].filters[0].list = []

        # Disable input coordinates if map extent is used
        if parameters[4].value:
            parameters[3].enabled = False
            parameters[5].enabled = False
        else:
            parameters[3].enabled = True
            parameters[5].enabled = True

        # Disable centoer of map extent if map extent is used
        if parameters[5].value:
            # parameters[3].enabled = False
            parameters[4].enabled = False
        else:
            # parameters[3].enabled = True
            parameters[4].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

        # Make sure property name is only used once
        prop_list = []
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            for row in val_list:
                prop_name = row[0]
                if prop_name not in prop_list:
                    prop_list.append(prop_name)
                else:
                    parameters[1].setErrorMessage(
                        f"The property name '{prop_name}' is used more than once. Please use unique property names."
                    )
                    return

    def execute(self, parameters, messages):
        """
        The source code of the tool.
        """
        asset_tag = parameters[0].valueAsText
        feat_color = parameters[6].valueAsText

        # point_shape= parameters[2].valueAsText
        # point_size = parameters[3].valueAsText
        # line_width = parameters[4].valueAsText
        # line_type  = parameters[5].valueAsText
        # fill_color = parameters[6].valueAsText
        # opacity    = parameters[7].valueAsText

        # Define visualization parameters
        vis_params = {}
        # Add color to vis_params if specified
        if feat_color:
            vis_params["color"] = feat_color
        # # Add point shape and size if specified
        # if point_shape :
        #     vis_params['pointShape'] = point_shape
        # if point_size :
        #     vis_params['pointSize'] = int(point_size)
        # # Add line width and type if specified
        # if line_width :
        #     vis_params['width'] = int(line_width)
        # if line_type :
        #     vis_params['lineType'] = line_type

        # # Add fill color and opacity if specified
        # if fill_color :
        #     vis_params['fillColor'] = fill_color
        # if opacity :
        #     vis_params['fillColorOpacity'] = float(opacity)

        # Get image by label
        fc = ee.FeatureCollection(asset_tag)

        # Filter by properties
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            # Could be multiple filter properties
            for row in val_list:
                prop_name = row[0]
                # property value could be integer, float or string
                try:
                    prop_val = int(row[2])
                except ValueError:
                    try:
                        prop_val = float(row[2])
                    except ValueError:
                        prop_val = row[2]
                operator = row[1]

                # Check if prop_val is a string and format accordingly
                if isinstance(prop_val, str):
                    # If prop_val is a string, wrap it in single quotes
                    filter_condition = "{} {} '{}'".format(
                        prop_name, operator, prop_val
                    )
                else:
                    # If prop_val is an integer or float, no quotes needed
                    filter_condition = "{} {} {}".format(prop_name, operator, prop_val)

                arcpy.AddMessage("Filter by property: " + filter_condition)
                fc = fc.filter(filter_condition)

        # Filter by dates if specified
        if parameters[2].valueAsText:
            val_list = parameters[2].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
            fc = fc.filterDate(start_date, end_date)

        # Filter by bounds if specified
        if parameters[4].value or parameters[5].value:  # Use map extent
            xmin, ymin, xmax, ymax = get_map_view_extent()
            # Filter by point
            if parameters[4].value:
                # Get the centroid of map extent
                lon = (xmin + xmax) / 2
                lat = (ymin + ymax) / 2
                fc = fc.filterBounds(ee.Geometry.Point((float(lon), float(lat))))
            else:  # filter by area
                roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
                fc = fc.filterBounds(roi)

        else:  # use input coordinates
            if parameters[3].valueAsText:
                val_list = parameters[3].values
                lon = val_list[0][0]
                lat = val_list[0][1]
                fc = fc.filterBounds(ee.Geometry.Point((float(lon), float(lat))))
            else:  # no filter by bounds
                lon = None
                lat = None

        # Feature collection could contain zero record after filters
        if fc.size().getInfo() > 0:
            # Get the map ID and token
            map_id_dict = fc.getMapId(vis_params)

            # Construct the URL
            map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

            # Add map URL to the current ArcMap
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.listMaps("Map")[0]
            tsl = aprxMap.addDataFromPath(map_url)
            tsl.name = asset_tag

            # Zoom to feature collection centroid if provided by dataset
            try:
                centroid_coords, bounds_coords = get_object_centroid(fc, 1)
                zoom_to_point(aprx, centroid_coords, bounds_coords)
            except:
                pass

            # Save object to serialized JSON file
            if parameters[7].valueAsText:
                out_json = parameters[7].valueAsText
                if not out_json.endswith(".json"):
                    out_json = out_json + ".json"
                arcgee.data.save_ee_result(fc, out_json)

        else:
            arcpy.AddWarning(
                "No data record returned after applying filters! Please reset the filters and try again."
            )

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Add GEE Feature Collection to Map by Serialized Object in JSON
class AddFeatCol2MapbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add Feature Collection to Map by Serialized Object"
        self.description = ""
        self.category = "Data Exploration Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """
        Define the tool parameters.

        vis_params = {
            "color": "000000",
            "pointShape": "circle",
            "pointSize": 3,
            "width": 2,
            "lineType": "solid",
            "fillColor": '00FF00',
            "opacity": 0.8,

            "colorOpacity": 1,
            "fillColorOpacity": 0.66,
        }
        """

        param0 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param0.filter.list = ["json"]

        param1 = arcpy.Parameter(
            name="current_tag",
            displayName="The asset tag of the selected object is shown below",
            datatype="GPString",
            direction="Input",
            multiValue=False,
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="color",
            displayName="Specify the color for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        # param2 = arcpy.Parameter(
        #     name="point_shape",
        #     displayName="Specify the point shape for visualization",
        #     datatype="GPString",
        #     direction="Input",
        #     parameterType="Optional")
        # param2.filter.list = ['circle','square','diamond','cross','plus','triangle']

        # param3 = arcpy.Parameter(
        #     name="point_size",
        #     displayName="Specify the point size for visualization",
        #     datatype="GPDouble",
        #     direction="Input",
        #     parameterType="Optional")
        # param3.filter.list = [2,4,6,8,10]

        # param4 = arcpy.Parameter(
        #     name="line_width",
        #     displayName="Specify the line width for visualization ",
        #     datatype="GPDouble",
        #     direction="Input",
        #     parameterType="Optional")
        # param4.filter.list = [1,2,3,4,5]

        # param5 = arcpy.Parameter(
        #     name="line_type",
        #     displayName="Specify the line type for visualization",
        #     datatype="GPString",
        #     direction="Input",
        #     parameterType="Optional")
        # param5.filter.list = ['solid','dotted','dashed']

        # param6 = arcpy.Parameter(
        #     name="fill_color",
        #     displayName="Specify the fill color of polygons for visualization",
        #     datatype="GPString",
        #     direction="Input",
        #     parameterType="Optional")

        # param7 = arcpy.Parameter(
        #     name="opacity",
        #     displayName="Specify the opacity for visualization",
        #     datatype="GPDouble",
        #     direction="Input",
        #     parameterType="Optional")
        # # Set the value range
        # param7.filter.type = "Range"
        # param7.filter.list = [0, 1]

        params = [param0, param1, param2]
        # ,param2,param3,param4,param5,param6,param7]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        json_path = parameters[0].valueAsText
        if json_path:
            fc = arcgee.data.load_ee_result(json_path)
            parameters[1].value = fc.get("system:id").getInfo()
        else:
            parameters[1].value = None

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """
        The source code of the tool.
        """
        json_path = parameters[0].valueAsText
        feat_color = parameters[2].valueAsText

        # load collection object
        fc = arcgee.data.load_ee_result(json_path)
        asset_tag = fc.get("system:id").getInfo()

        # point_shape= parameters[2].valueAsText
        # point_size = parameters[3].valueAsText
        # line_width = parameters[4].valueAsText
        # line_type  = parameters[5].valueAsText
        # fill_color = parameters[6].valueAsText
        # opacity    = parameters[7].valueAsText

        # Define visualization parameters
        vis_params = {}
        # Add color to vis_params if specified
        if feat_color:
            vis_params["color"] = feat_color

        # # Add point shape and size if specified
        # if point_shape :
        #     vis_params['pointShape'] = point_shape
        # if point_size :
        #     vis_params['pointSize'] = int(point_size)
        # # Add line width and type if specified
        # if line_width :
        #     vis_params['width'] = int(line_width)
        # if line_type :
        #     vis_params['lineType'] = line_type

        # # Add fill color and opacity if specified
        # if fill_color :
        #     vis_params['fillColor'] = fill_color
        # if opacity :
        #     vis_params['fillColorOpacity'] = float(opacity)

        # Feature collection could contain zero record after filters
        if fc.size().getInfo() > 0:
            # Get the map ID and token
            map_id_dict = fc.getMapId(vis_params)

            # Construct the URL
            map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

            # Add map URL to the current ArcMap
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.listMaps("Map")[0]
            tsl = aprxMap.addDataFromPath(map_url)
            tsl.name = asset_tag

            # Zoom to feature collection centroid if provided by dataset
            try:
                centroid_coords, bounds_coords = get_object_centroid(fc, 1)
                zoom_to_point(aprx, centroid_coords, bounds_coords)
            except:
                pass

        else:
            arcpy.AddWarning(
                "No data record returned after applying filters! Please reset the filters and try again."
            )

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


""" Data Management Tools """


# Download GEE Image by Asset Tag (through XEE + RasterIO)
class DownloadImgbyTag:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Image by Asset Tag"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Image collection inputs are optional
        param0 = arcpy.Parameter(
            name="asset_tag",
            displayName="Specify the image asset tag",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Select the bands",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="scale",
            displayName="Specify the scale",
            datatype="GPDouble",
            direction="Input",
            multiValue=False,
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a polygon as region of interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the current map view extent as region of interest",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="out_tiff",
            displayName="Specify the output file name",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param5.filter.list = ["tif"]

        param6 = arcpy.Parameter(
            name="load_tiff",
            displayName="Load images to map after download",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
        ]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        img_tag = parameters[0].valueAsText
        # Update only when filter list is empty
        if img_tag and not parameters[1].filter.list:
            image = ee.Image(img_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display
            band_res_list = []
            for iband in band_list:
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
            parameters[1].filter.list = band_res_list

        # Reset band filter list when asset tag changes
        if not parameters[0].valueAsText:
            parameters[1].filter.list = []

        # Capture the suggested scale value based on selected bands
        band_str = parameters[1].valueAsText
        if band_str and not parameters[2].value:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            scale_only = [float(iband.split("--")[1]) for iband in bands]
            # use the maximum scale of the selected band by default
            parameters[2].value = max(scale_only)

        # Disable input feature if map extent is used
        if parameters[4].value:  # map extent selected
            parameters[3].enabled = False
        else:
            parameters[3].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        import rasterio
        from rasterio.transform import from_origin

        """The source code of the tool."""
        # Multiple images could be selected
        asset_tag = parameters[0].valueAsText
        band_str = parameters[1].valueAsText
        scale = parameters[2].valueAsText
        in_poly = parameters[3].valueAsText
        use_extent = parameters[4].valueAsText
        out_tiff = parameters[5].valueAsText
        load_tiff = parameters[6].valueAsText

        # Filter image by bands if specified
        # Remove ' in band string in case user adds it
        if "'" in band_str:
            band_str = band_str.replace("'", "")
        bands = band_str.split(";")
        bands_only = [iband.split("--")[0] for iband in bands]
        arcpy.AddMessage("Bands selected: " + ",".join(bands_only))

        # make sure output file ends with tif
        if not out_tiff.endswith(".tif"):
            out_tiff = out_tiff + ".tif"

        # Check image projection
        image = ee.Image(asset_tag)

        # Get the region of interests
        # Use map view extent if checked
        if use_extent == "true":
            xmin, ymin, xmax, ymax = get_map_view_extent()
            roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
        # Use input feature layer as ROI
        else:
            # Get input feature coordinates to list
            coords = get_polygon_coords(in_poly)
            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)

        # Get the scale for xarray dataset
        scale_ds = float(scale)

        # Get crs for xarray metadata
        # crs information could be missing, then use wkt from projection
        try:
            crs = image.select(0).projection().getInfo()["crs"]
            arcpy.AddMessage("Image projection CRS is " + crs)
        except:
            # crs is not explictly defined
            arcpy.AddMessage("Image projection CRS is unknown. Use WKT instead.")
            wkt = image.select(0).projection().getInfo()["wkt"]
            crs = rasterio.crs.CRS.from_wkt(wkt)

        # Download image by tag
        img_tag = asset_tag
        arcpy.AddMessage("Download image: " + img_tag + " ...")
        # Must be image collection to convert to xarray
        image = ee.ImageCollection(ee.Image(img_tag))
        # Filter image by selected bands
        image = image.select(bands_only)

        # check if use projection
        use_projection = whether_use_projection(image)
        # download image as geotiff
        image_to_geotiff(
            image, bands_only, crs, scale_ds, roi, use_projection, out_tiff
        )

        # Add out tiff to map layer
        if load_tiff == "true":
            arcpy.AddMessage("Load image to map ...")
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.activeMap
            aprxMap.addDataFromPath(out_tiff)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download GEE Image by Serialized JSON Object (through XEE + RasterIO)
class DownloadImgbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Image by Serialized Object"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized image object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param0.filter.list = ["json"]

        param1 = arcpy.Parameter(
            name="current_tag",
            displayName="The asset tag of the selected object is shown below",
            datatype="GPString",
            direction="Input",
            multiValue=False,
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="bands",
            displayName="Select the bands",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="scale",
            displayName="Specify the scale",
            datatype="GPDouble",
            direction="Input",
            multiValue=False,
            parameterType="Required",
        )

        param4 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a polygon as region of interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the current map view extent as region of interest",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="out_tiff",
            displayName="Specify the output file name",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param6.filter.list = ["tif"]

        param7 = arcpy.Parameter(
            name="load_tiff",
            displayName="Load images to map after download",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
            param7,
        ]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        json_path = parameters[0].valueAsText
        if json_path:
            # Display the asset tag of the selected object
            image = arcgee.data.load_ee_result(json_path)
            parameters[1].value = image.get("system:id").getInfo()

            # Update only when band filter list is empty
            if not parameters[2].filter.list:
                band_names = image.bandNames()
                band_list = band_names.getInfo()
                # Add band resolution information to display
                band_res_list = []
                for iband in band_list:
                    band_tmp = image.select(iband)
                    proj = band_tmp.projection()
                    res = proj.nominalScale().getInfo()
                    band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
                parameters[2].filter.list = band_res_list

        # Reset band filter list when asset tag changes
        if not json_path:
            parameters[1].value = None
            parameters[2].filter.list = []

        # Capture the suggested scale value based on selected bands
        band_str = parameters[2].valueAsText
        if band_str and not parameters[3].value:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            scale_only = [float(iband.split("--")[1]) for iband in bands]
            # use the maximum scale of the selected band by default
            parameters[3].value = max(scale_only)

        # Disable input feature if map extent is used
        if parameters[5].value:  # map extent selected
            parameters[4].enabled = False
        else:
            parameters[4].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        import rasterio
        from rasterio.transform import from_origin

        """The source code of the tool."""
        # Multiple images could be selected
        json_path = parameters[0].valueAsText
        band_str = parameters[2].valueAsText
        scale = parameters[3].valueAsText
        in_poly = parameters[4].valueAsText
        use_extent = parameters[5].valueAsText
        out_tiff = parameters[6].valueAsText
        load_tiff = parameters[7].valueAsText

        # Filter image by bands if specified
        # Remove ' in band string in case user adds it
        if "'" in band_str:
            band_str = band_str.replace("'", "")
        bands = band_str.split(";")
        bands_only = [iband.split("--")[0] for iband in bands]
        arcpy.AddMessage("Bands selected: " + ",".join(bands_only))

        # Make sure output file ends with tif
        if not out_tiff.endswith(".tif"):
            out_tiff = out_tiff + ".tif"

        # Check image projection
        image = arcgee.data.load_ee_result(json_path)

        # Get the region of interests
        # Use map view extent if checked
        if use_extent == "true":
            xmin, ymin, xmax, ymax = get_map_view_extent()
            roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
        # Use input feature layer as ROI
        else:
            # Get input feature coordinates to list
            coords = get_polygon_coords(in_poly)
            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)

        # Get the scale for xarray dataset
        scale_ds = float(scale)

        # Get crs for xarray metadata
        # crs information could be missing, then use wkt from projection
        try:
            crs = image.select(0).projection().getInfo()["crs"]
            arcpy.AddMessage("Image projection CRS is " + crs)
        except:
            # crs is not explictly defined
            arcpy.AddMessage("Image projection CRS is unknown. Use WKT instead.")
            wkt = image.select(0).projection().getInfo()["wkt"]
            crs = rasterio.crs.CRS.from_wkt(wkt)

        # Download image by tag
        img_tag = image.get("system:id").getInfo()
        arcpy.AddMessage("Download image: " + img_tag + " ...")
        # Must be image collection to convert to xarray
        image = ee.ImageCollection(ee.Image(img_tag))
        # Filter image by selected bands
        image = image.select(bands_only)

        # check if use projection
        use_projection = whether_use_projection(image)
        # download image as geotiff
        image_to_geotiff(
            image, bands_only, crs, scale_ds, roi, use_projection, out_tiff
        )

        # Add out tiff to map layer
        if load_tiff == "true":
            arcpy.AddMessage("Load image to map ...")
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.activeMap
            aprxMap.addDataFromPath(out_tiff)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download GEE Image Collection by Asset Tag (XEE + RasterIO)
class DownloadImgColbyTag:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Image Collection by Asset Tag"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Image collection inputs are optional
        param0 = arcpy.Parameter(
            name="ic_asset_tag",
            displayName="Specify the image collection asset tag",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param1.columns = [["GPString", "Starting Date"], ["GPString", "Ending Date"]]
        param1.value = [["2014-03-01", "2014-05-01"]]

        param2 = arcpy.Parameter(
            name="filter_bounds",
            displayName="Filter by location in coordinates",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param2.columns = [["GPString", "Longitude"], ["GPString", "Latitude"]]

        param3 = arcpy.Parameter(
            name="use_centroid",
            displayName="Use the center of the current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="img_list",
            displayName="Select images to download",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param5 = arcpy.Parameter(
            name="bands",
            displayName="Select the bands",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param6 = arcpy.Parameter(
            name="scale",
            displayName="Specify the scale",
            datatype="GPDouble",
            direction="Input",
            multiValue=False,
            parameterType="Required",
        )

        param7 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a polygon as region of interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param8 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the current map view extent as region of interest",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param9 = arcpy.Parameter(
            name="out_folder",
            displayName="Specify the output folder",
            datatype="DEFolder",
            direction="Input",
            parameterType="Required",
        )

        param10 = arcpy.Parameter(
            name="load_tiff",
            displayName="Load images to map after download",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
            param7,
            param8,
            param9,
            param10,
        ]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Get the filter dates
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
        else:
            start_date = None
            end_date = None

        # Get the filter bounds
        if parameters[3].value:  # use map extent
            # Disable input coordinates if map extent is used
            parameters[2].enabled = False
            xmin, ymin, xmax, ymax = get_map_view_extent()
            # Get the centroid of map extent
            lon = (xmin + xmax) / 2
            lat = (ymin + ymax) / 2
        else:  # use input lat/lon
            parameters[2].enabled = True
            if parameters[2].valueAsText:
                val_list = parameters[2].values
                lon = val_list[0][0]
                lat = val_list[0][1]
            else:
                lon = None
                lat = None

        # Check image list of a given collection asset
        asset_tag = parameters[0].valueAsText

        # Image collection size could be huge, may take long time to load image IDs without filters
        # Only retrieve the list of images, when either filter dates or filter bounds are selected
        if asset_tag and ((start_date and end_date) or (lon and lat)):
            collection = ee.ImageCollection(asset_tag)
            # Filter image collection as specified
            if lon is not None and lat is not None:
                collection = collection.filterBounds(
                    ee.Geometry.Point((float(lon), float(lat)))
                )
            if start_date is not None and end_date is not None:
                collection = collection.filterDate(start_date, end_date)
            # Get image IDs from collection
            image_ids = collection.aggregate_array("system:index").getInfo()
            parameters[4].filter.list = image_ids

        # Check the band list of the first selected image, assuming all selected images have the same bands
        img_ids = parameters[4].valueAsText
        # Update only when filter list is empty
        if img_ids and not parameters[5].filter.list:
            # Get the first select image
            img_id = img_ids.split(";")[0]
            # Only initialize ee when image asset tag is given
            if asset_tag:
                img_tag = asset_tag + "/" + img_id
            else:
                img_tag = img_id
            image = ee.Image(img_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display
            band_res_list = []
            for iband in band_list:
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
            parameters[5].filter.list = band_res_list

        # Reset band filter list when asset tag changes
        if (not parameters[4].valueAsText) and (not parameters[0].valueAsText):
            parameters[5].filter.list = []

        # Capture the suggested scale value based on selected bands
        band_str = parameters[5].valueAsText
        if band_str and not parameters[6].value:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            scale_only = [float(iband.split("--")[1]) for iband in bands]
            parameters[6].value = max(scale_only)

        # Disable input feature if map extent is used
        if parameters[8].value:  # map extent selected
            parameters[7].enabled = False
        else:
            parameters[7].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        import rasterio
        from rasterio.transform import from_origin

        """The source code of the tool."""
        # Multiple images could be selected
        asset_tag = parameters[0].valueAsText
        img_ids = parameters[4].valueAsText
        band_str = parameters[5].valueAsText
        scale = parameters[6].valueAsText
        in_poly = parameters[7].valueAsText
        use_extent = parameters[8].valueAsText
        out_folder = parameters[9].valueAsText
        load_tiff = parameters[10].valueAsText

        img_id_list = img_ids.split(";")

        # Filter image by bands if specified
        # Remove ' in band string in case user adds it
        if "'" in band_str:
            band_str = band_str.replace("'", "")
        bands = band_str.split(";")
        bands_only = [iband.split("--")[0] for iband in bands]
        arcpy.AddMessage("Bands selected: " + ",".join(bands_only))

        # Get the region of interests
        # Use map view extent if checked
        if use_extent == "true":
            xmin, ymin, xmax, ymax = get_map_view_extent()
            roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
        # Use input feature layer as ROI
        else:
            # Get input feature coordinates to list
            coords = get_polygon_coords(in_poly)
            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)

        # Get the scale for xarray dataset
        scale_ds = float(scale)

        # Check first image projection
        image = ee.Image(asset_tag + "/" + img_id_list[0])

        # Get crs code for xarray metadata
        # crs information could be missing, then use wkt from projection
        try:
            crs = image.select(0).projection().getInfo()["crs"]
            arcpy.AddMessage("Image projection CRS is " + crs)
        except:
            # crs is not explictly defined
            arcpy.AddMessage("Image projection CRS is unknown.")
            wkt = image.select(0).projection().getInfo()["wkt"]
            crs = rasterio.crs.CRS.from_wkt(wkt)

        # Check if use projection or crs code
        image = ee.ImageCollection(image)
        use_projection = whether_use_projection(image)

        out_tiff_list = []
        # Iterate each selected image
        for img_id in img_id_list:
            # For image collection, concatenate to get the image asset tag
            img_tag = asset_tag + "/" + img_id

            # Create output file name based on image tags
            out_tiff = os.path.join(out_folder, img_tag.replace("/", "_") + ".tif")
            out_tiff_list.append(out_tiff)

            arcpy.AddMessage("Download image: " + img_tag + " ...")
            # Must be image collection to convert to xarray
            image = ee.ImageCollection(ee.Image(img_tag))
            # Filter image by selected bands
            image = image.select(bands_only)

            # download image as geotiff
            image_to_geotiff(
                image, bands_only, crs, scale_ds, roi, use_projection, out_tiff
            )

        # Add out tiff to map layer
        if load_tiff == "true":
            arcpy.AddMessage("Load image to map ...")
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.activeMap
            for out_tiff in out_tiff_list:
                aprxMap.addDataFromPath(out_tiff)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download GEE Image Collection by Serialized JSON Object (XEE + RasterIO)
class DownloadImgColbyObj:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Image Collection by Serialized Object"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="ee_obj",
            displayName="Select the JSON file of the serialized image collection object",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        # only displays JSON files
        param0.filter.list = ["json"]

        param1 = arcpy.Parameter(
            name="current_tag",
            displayName="The asset tag of the selected object is shown below",
            datatype="GPString",
            direction="Input",
            multiValue=False,
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="img_list",
            displayName="Select images to download",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="bands",
            displayName="Select the bands",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param4 = arcpy.Parameter(
            name="scale",
            displayName="Specify the scale",
            datatype="GPDouble",
            direction="Input",
            multiValue=False,
            parameterType="Required",
        )

        param5 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a polygon as region of interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the current map view extent as region of interest",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param7 = arcpy.Parameter(
            name="out_folder",
            displayName="Specify the output folder",
            datatype="DEFolder",
            direction="Input",
            parameterType="Required",
        )

        param8 = arcpy.Parameter(
            name="load_tiff",
            displayName="Load images to map after download",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
            param7,
            param8,
        ]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        json_path = parameters[0].valueAsText
        if json_path:
            collection = arcgee.data.load_ee_result(json_path)
            # Display the asset tag of selected object
            parameters[1].value = collection.get("system:id").getInfo()

            # Only fill the image id filter list when it is empty
            if not parameters[2].filter.list:
                # Get image IDs from collection
                image_ids = collection.aggregate_array("system:index").getInfo()
                parameters[2].filter.list = image_ids

            # Check band list of the selected image
            img_ids = parameters[2].valueAsText
            # Update only when filter list is empty
            if img_ids and not parameters[3].filter.list:
                # Get the first select image
                img_id = img_ids.split(";")[0]
                # retrieve image tag from collection
                asset_tag = collection.get("system:id").getInfo()
                img_tag = asset_tag + "/" + img_id
                image = ee.Image(img_tag)
                band_names = image.bandNames()
                band_list = band_names.getInfo()
                # Add band resolution information to display
                band_res_list = []
                for iband in band_list:
                    band_tmp = image.select(iband)
                    proj = band_tmp.projection()
                    res = proj.nominalScale().getInfo()
                    band_res_list.append(iband + "--" + str(round(res, 1)) + "--m")
                parameters[3].filter.list = band_res_list

        # Reset image filter list
        if not json_path:
            parameters[1].value = None
            parameters[2].filter.list = []

        # Reset band filter list when asset tag changes
        if (not parameters[2].valueAsText) and (not json_path):
            parameters[3].filter.list = []

        # Capture the suggested scale value based on selected bands
        band_str = parameters[3].valueAsText
        if band_str and not parameters[4].value:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            scale_only = [float(iband.split("--")[1]) for iband in bands]
            parameters[4].value = max(scale_only)

        # Disable input feature if map extent is used
        if parameters[6].value:  # map extent selected
            parameters[5].enabled = False
        else:
            parameters[5].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        import rasterio
        from rasterio.transform import from_origin

        """The source code of the tool."""
        # Multiple images could be selected
        json_path = parameters[0].valueAsText
        img_ids = parameters[2].valueAsText
        band_str = parameters[3].valueAsText
        scale = parameters[4].valueAsText
        in_poly = parameters[5].valueAsText
        use_extent = parameters[6].valueAsText
        out_folder = parameters[7].valueAsText
        load_tiff = parameters[8].valueAsText

        # load collection object
        collection = arcgee.data.load_ee_result(json_path)
        # Get image tag for layer name
        asset_tag = collection.get("system:id").getInfo()

        img_id_list = img_ids.split(";")

        # Filter image by bands if specified
        # Remove ' in band string in case user adds it
        if "'" in band_str:
            band_str = band_str.replace("'", "")
        bands = band_str.split(";")
        bands_only = [iband.split("--")[0] for iband in bands]
        arcpy.AddMessage("Bands selected: " + ",".join(bands_only))

        # Get the region of interests
        # Use map view extent if checked
        if use_extent == "true":
            xmin, ymin, xmax, ymax = get_map_view_extent()
            roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
        # Use input feature layer as ROI
        else:
            # Get input feature coordinates to list
            coords = get_polygon_coords(in_poly)
            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)

        # Get the scale for xarray dataset
        scale_ds = float(scale)

        # Check first image projection
        image = ee.Image(asset_tag + "/" + img_id_list[0])

        # Get crs code for xarray metadata
        # crs information could be missing, then use wkt from projection
        try:
            crs = image.select(0).projection().getInfo()["crs"]
            arcpy.AddMessage("Image projection CRS is " + crs)
        except:
            # crs is not explictly defined
            arcpy.AddMessage("Image projection CRS is unknown.")
            wkt = image.select(0).projection().getInfo()["wkt"]
            crs = rasterio.crs.CRS.from_wkt(wkt)

        # Check if use projection or crs code
        image = ee.ImageCollection(image)
        use_projection = whether_use_projection(image)

        out_tiff_list = []
        # Iterate each selected image
        for img_id in img_id_list:
            # For image collection, concatenate to get the image asset tag
            img_tag = asset_tag + "/" + img_id

            # Create output file name based on image tags
            out_tiff = os.path.join(out_folder, img_tag.replace("/", "_") + ".tif")
            out_tiff_list.append(out_tiff)

            arcpy.AddMessage("Download image: " + img_tag + " ...")
            # Must be image collection to convert to xarray
            image = ee.ImageCollection(ee.Image(img_tag))
            # Filter image by selected bands
            image = image.select(bands_only)

            # download image as geotiff
            image_to_geotiff(
                image, bands_only, crs, scale_ds, roi, use_projection, out_tiff
            )

        # Add out tiff to map layer
        if load_tiff == "true":
            arcpy.AddMessage("Load image to map ...")
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.activeMap
            for out_tiff in out_tiff_list:
                aprxMap.addDataFromPath(out_tiff)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download Image Collection to GIF
class DownloadImgCol2Gif:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Image Collection to GIF"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Image collection inputs are optional
        param0 = arcpy.Parameter(
            name="ic_asset_tag",
            displayName="Specify the image collection asset tag",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param1.columns = [["GPString", "Starting Date"], ["GPString", "Ending Date"]]
        param1.value = [["2014-03-01", "2014-05-01"]]

        param2 = arcpy.Parameter(
            name="filter_bounds",
            displayName="Filter by location in coordinates",
            datatype="GPValueTable",
            direction="Input",
            parameterType="Optional",
        )
        param2.columns = [["GPString", "Longitude"], ["GPString", "Latitude"]]

        param3 = arcpy.Parameter(
            name="use_centroid",
            displayName="Use the center of the current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="bands",
            displayName="Select the bands of the gif (maximum 3)",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param5 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a polygon as region of interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param6 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the current map view extent as region of interest",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param7 = arcpy.Parameter(
            name="dims",
            displayName="Specify the dimensions of the gif",
            datatype="GPDouble",
            direction="Input",
            parameterType="Required",
        )
        param7.value = 768

        param8 = arcpy.Parameter(
            name="fps",
            displayName="Specify the frames per second of the gif",
            datatype="GPDouble",
            direction="Input",
            parameterType="Required",
        )
        param8.value = 10

        param9 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param10 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param11 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param12 = arcpy.Parameter(
            name="out_gif",
            displayName="Specify the output gif file name",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        params = [
            param0,
            param1,
            param2,
            param3,
            param4,
            param5,
            param6,
            param7,
            param8,
            param9,
            param10,
            param11,
            param12,
        ]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Define a function to project a point to WGS 84 (EPSG 4326)
        def project_to_wgs84(x, y, in_spatial_ref):
            point = arcpy.Point(x, y)
            point_geom = arcpy.PointGeometry(point, in_spatial_ref)
            wgs84 = arcpy.SpatialReference(4326)
            point_geom_wgs84 = point_geom.projectAs(wgs84)
            return point_geom_wgs84.centroid.X, point_geom_wgs84.centroid.Y

        # Get the filter dates
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
        else:
            start_date = None
            end_date = None

        # Get the filter bounds
        if parameters[3].value:  # use map extent
            # Disable input coordinates if map extent is used
            parameters[2].enabled = False
            xmin, ymin, xmax, ymax = get_map_view_extent()
            # Get the centroid of map extent
            lon = (xmin + xmax) / 2
            lat = (ymin + ymax) / 2
        else:  # use input lat/lon
            parameters[2].enabled = True
            if parameters[2].valueAsText:
                val_list = parameters[2].values
                lon = val_list[0][0]
                lat = val_list[0][1]
            else:
                lon = None
                lat = None

        # Check image list of a given collection asset
        asset_tag = parameters[0].valueAsText

        # Get image collection
        if asset_tag:
            collection = ee.ImageCollection(asset_tag)
            # Filter image collection as specified
            if lon is not None and lat is not None:
                collection = collection.filterBounds(
                    ee.Geometry.Point((float(lon), float(lat)))
                )
            if start_date is not None and end_date is not None:
                collection = collection.filterDate(start_date, end_date)

            # Check the band list of the first selected image, assuming all selected images have the same bands
            # Update only when filter list is empty
            if not parameters[4].filter.list:
                # Get the first select image
                image = collection.first()
                band_names = image.bandNames()
                band_list = band_names.getInfo()
                # Add band resolution information to display
                band_res_list = []
                for iband in band_list:
                    band_tmp = image.select(iband)
                    proj = band_tmp.projection()
                    res = proj.nominalScale().getInfo()
                    band_res_list.append(iband + "--" + str(round(res)) + "--m")
                parameters[4].filter.list = band_res_list

        # Reset band filter list when asset tag changes
        if not parameters[0].valueAsText:
            parameters[4].filter.list = []

        # Disable input feature if map extent is used
        if parameters[6].value:  # map extent selected
            parameters[5].enabled = False
        else:
            parameters[5].enabled = True

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Multiple images could be selected
        asset_tag = parameters[0].valueAsText
        band_str = parameters[4].valueAsText
        in_poly = parameters[5].valueAsText
        use_extent = parameters[6].valueAsText
        dims = parameters[7].valueAsText
        fps = parameters[8].valueAsText
        min_val = parameters[9].valueAsText
        max_val = parameters[10].valueAsText
        palette_str = parameters[11].valueAsText
        out_gif = parameters[12].valueAsText

        # Define a function to project a point to WGS 84 (EPSG 4326)
        def project_to_wgs84(x, y, in_spatial_ref):
            point = arcpy.Point(x, y)
            point_geom = arcpy.PointGeometry(point, in_spatial_ref)
            wgs84 = arcpy.SpatialReference(4326)
            point_geom_wgs84 = point_geom.projectAs(wgs84)
            return point_geom_wgs84.centroid.X, point_geom_wgs84.centroid.Y

        # Get the filter dates
        if parameters[1].valueAsText:
            val_list = parameters[1].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
        else:
            start_date = None
            end_date = None

        # Get the filter bounds
        if parameters[3].value:  # use map extent
            # Disable input coordinates if map extent is used
            parameters[2].enabled = False
            xmin, ymin, xmax, ymax = get_map_view_extent()
            # Get the centroid of map extent
            lon = (xmin + xmax) / 2
            lat = (ymin + ymax) / 2
        else:  # use input lat/lon
            parameters[2].enabled = True
            if parameters[2].valueAsText:
                val_list = parameters[2].values
                lon = val_list[0][0]
                lat = val_list[0][1]
            else:
                lon = None
                lat = None

        # Get image collection
        collection = ee.ImageCollection(asset_tag)
        # Filter image collection as specified
        if lon is not None and lat is not None:
            collection = collection.filterBounds(
                ee.Geometry.Point((float(lon), float(lat)))
            )
        if start_date is not None and end_date is not None:
            collection = collection.filterDate(start_date, end_date)
        # Set limit
        # collection = collection.limit(24)

        # Define animation function parameters
        videoArgs = {}

        # Add bands to videoArgs if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            # Ignore the resolution part
            videoArgs["bands"] = bands_only

        # Add dimensions and frames per second if specified
        if dims:
            videoArgs["dimensions"] = int(dims)
        if fps:
            videoArgs["framesPerSecond"] = int(fps)

        # Add min and max values if specified
        if min_val:
            videoArgs["min"] = float(min_val)
        if max_val:
            videoArgs["max"] = float(max_val)

        # Add color palette if specified
        if palette_str:
            # arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str:
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified
            palette = palette_str.split(",")
            # arcpy.AddMessage(palette)
            videoArgs["palette"] = palette

        # Get the region of interests
        # Use map view extent if checked
        if use_extent == "true":  # use map view
            xmin, ymin, xmax, ymax = get_map_view_extent()
            roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
        # Use input feature layer as ROI
        else:
            spatial_ref = arcpy.Describe(in_poly).spatialReference
            poly_prj = spatial_ref.PCSCode
            if poly_prj == 0:
                poly_prj = spatial_ref.GCSCode
            arcpy.AddMessage("Input feature layer projection is " + str(poly_prj))

            # Project input feature to GEE image coordinate system if needed
            target_poly = in_poly
            if str(poly_prj) not in "EPSG:4326":
                arcpy.AddMessage("Projecting input feature layer to EPSG:4326 ...")
                out_sr = arcpy.SpatialReference(4326)
                arcpy.Project_management(in_poly, "poly_temp", out_sr)
                target_poly = "poly_temp"

            # convert input feature to geojson
            arcpy.FeaturesToJSON_conversion(
                target_poly, "temp.geojson", "FORMATTED", "", "", "GEOJSON"
            )

            # Read the GeoJSON file
            upper_path = os.path.dirname(arcpy.env.workspace)
            file_geojson = os.path.join(upper_path, "temp.geojson")
            with open(file_geojson) as f:
                geojson_data = json.load(f)

            # Collect polygon object coordinates
            coords = []
            for feature in geojson_data["features"]:
                coords.append(feature["geometry"]["coordinates"])
            arcpy.AddMessage("Total number of polygon objects: " + str(len(coords)))

            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)
            # Delete temporary geojson
            arcpy.management.Delete(file_geojson)

        # Get the region of interest
        videoArgs["regions"] = roi
        # Use the crs code from the first selected band
        crs = collection.first().select(0).projection().getInfo()["crs"]
        arcpy.AddMessage("Image asset projection is " + crs)
        videoArgs["crs"] = crs

        # Download filtered image collection to GIF
        try:
            arcpy.AddMessage("Generating URL...")
            url = collection.getVideoThumbURL(videoArgs)

            arcpy.AddMessage(f"Downloading GIF image from {url}\nPlease wait ...")
            r = requests.get(url, stream=True, timeout=300)

            if r.status_code != 200:
                arcpy.AddMessage("An error occurred while downloading.")
                arcpy.AddMessage(r.json()["error"]["message"])
                return
            else:
                with open(out_gif, "wb") as fd:
                    for chunk in r.iter_content(chunk_size=1024):
                        fd.write(chunk)
                arcpy.AddMessage(f"The GIF image has been saved to: {out_gif}")
        except Exception as e:
            arcpy.AddMessage(e)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Save GEE Asset to Serialized JSON File
class SaveAsset2JSON:
    def __init__(self):
        self.label = "Save Earth Engine Asset to Serialized JSON File"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            displayName="Specify the asset tag",
            name="asset_tag",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        param1 = arcpy.Parameter(
            displayName="Select the type of the Earth Engine asset",
            name="asset_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        param1.filter.list = ["FeatureCollection", "Image", "ImageCollection"]

        param2 = arcpy.Parameter(
            name="out_json",
            displayName="Specify the output JSON file",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        param2.filter.list = ["json"]

        params = [param0, param1, param2]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        asset_tag = parameters[0].valueAsText
        data_type = parameters[1].valueAsText
        out_json = parameters[2].valueAsText

        if not out_json.endswith(".json"):
            out_json = out_json + ".json"

        # Retrieve the Earth Engine object based on the asset tag and data type
        if data_type == "FeatureCollection":
            ee_object = ee.FeatureCollection(asset_tag)
        elif data_type == "Image":
            ee_object = ee.Image(asset_tag)
        elif data_type == "ImageCollection":
            ee_object = ee.ImageCollection(asset_tag)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        arcgee.data.save_ee_result(ee_object, out_json)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Upload Files to Google Cloud Storage and Convert to GEE Asset
class Upload2GCS:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Upload File to Cloud Storage and Convert to Earth Engine Asset"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="project_id",
            displayName="Specify the Google Cloud project ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="bucket_name",
            displayName="Select the storage bucket name",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="bucket_folder",
            displayName="Select the folder within the bucket",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="files",
            displayName="Choose a local file to upload",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
            multiValue=True,
        )

        param3.filter.list = ["tif", "shp", "csv", "zip", "tfrecord"]

        param4 = arcpy.Parameter(
            name="upload_asset",
            displayName="Upload the file to Earth Engine",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="asset_type",
            displayName="Choose asset type",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param5.value = "image"
        param5.filter.list = ["image", "table"]

        param6 = arcpy.Parameter(
            name="asset_id",
            displayName="Specify asset id",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )
        param6.value = "Not-in-Use"

        params = [param0, param1, param2, param3, param4, param5, param6]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Get the project ID first
        if parameters[0].valueAsText:
            project_id = parameters[0].valueAsText
            # Initialize a Cloud Storage client, for only once
            if not hasattr(self, "storage_client"):
                self.storage_client = storage.Client(project=project_id)

            # Get the list of all bucket names in this project
            buckets = self.storage_client.list_buckets()
            bucket_names = []
            for bucket in buckets:
                bucket_names.append(bucket.name)

            # Add bucket names to filter list
            parameters[1].filter.list = bucket_names

            # When bucket name is selected, list all available folders
            if parameters[1].valueAsText:
                bucket_name = parameters[1].valueAsText
                parameters[2].filter.list = list_folders_recursive(
                    self.storage_client, bucket_name
                )

        # Enable additional input when uploading to earth engine checked
        if parameters[4].value:
            parameters[5].enabled = True
            parameters[6].enabled = True
            # give a default asset ID when project ID is provided
            if parameters[0].valueAsText and not parameters[6].valueAsText:
                parameters[6].value = (
                    "projects/" + parameters[0].valueAsText + "/assets/"
                )
        else:
            parameters[5].enabled = False
            parameters[6].enabled = False

        # reset input values
        if not parameters[0].valueAsText:
            parameters[1].value = None
            parameters[2].value = None
            parameters[6].value = None

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Read input parameters
        bucket_name = parameters[1].valueAsText
        bucket_folder = parameters[2].valueAsText
        files = parameters[3].valueAsText

        storage_client = storage.Client(project=parameters[0].valueAsText)

        # If user creates a new folder, make sure it ends with /
        if not bucket_folder.endswith("/"):
            bucket_folder = bucket_folder + "/"

        # Get the list of selected files
        # Remove ' in files in case users add it
        if "'" in files:
            files = files.replace("'", "")
        file_list = files.split(";")

        # Upload files to the selected bucket name
        gcs_file_list = []
        for ifile in file_list:
            file_name = os.path.basename(ifile)
            out_file = bucket_folder + file_name
            upload_to_gcs_bucket(storage_client, bucket_name, ifile, out_file)
            gcs_file_list.append(out_file)
            # check file extension
            file_extension = os.path.splitext(file_name)[1]
            # For shape file, need to upload accessary files
            if file_extension == ".shp":
                for extension in [".shx", ".dbf", ".prj", ".cpg"]:
                    upload_to_gcs_bucket(
                        storage_client,
                        bucket_name,
                        ifile.replace(".shp", extension),
                        out_file.replace(".shp", extension),
                    )

        # Upload file to earth engine
        if parameters[4].value:
            asset_type = parameters[5].valueAsText
            asset_id = parameters[6].valueAsText
            is_col = False

            # If more than one file is selected, treat as collection asset
            if len(gcs_file_list) > 1:
                is_col = True
                # use input asset id as folder path
                collection_asset_folder = asset_id
                # for image asset type, create image collection
                if asset_type == "image":
                    if not asset_exists(collection_asset_folder):
                        create_image_collection(collection_asset_folder)
                    else:
                        arcpy.AddMessage("The image collection already exists.")
                # if table, create a folder, all files will be uploaded to this folder
                else:
                    if not asset_exists(collection_asset_folder):
                        create_ee_folder(collection_asset_folder)
                    else:
                        arcpy.AddMessage("The folder already exists.")

            for ifile in gcs_file_list:
                # get file URI (file could be URI or relative path)
                bucket_uri = "gs://" + bucket_name + "/" + ifile
                # check if collection
                if is_col:
                    # upload to collection folder
                    # use file name as item id
                    file_name = os.path.splitext(os.path.basename(bucket_uri))[0]
                    item_id = f"{collection_asset_folder}/{file_name}"
                    gcs_file_to_ee_asset(asset_type, item_id, bucket_uri)
                else:
                    gcs_file_to_ee_asset(asset_type, asset_id, bucket_uri)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Convert GCS File to GEE Asset
class GCSFile2Asset:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Convert Cloud Storage File to Earth Engine Asset"
        self.description = ""
        self.category = "Data Management Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="project_id",
            displayName="Specify the Google Cloud project ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param1 = arcpy.Parameter(
            name="bucket_name",
            displayName="Select the storage bucket name",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="bucket_folder",
            displayName="Select the folder within the bucket",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param3 = arcpy.Parameter(
            name="files",
            displayName="Select the file within the folder or specify the gsutil URI",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
            multiValue=True,
        )

        param4 = arcpy.Parameter(
            name="asset_type",
            displayName="Choose the asset type",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param4.value = "image"
        param4.filter.list = ["image", "table"]

        param5 = arcpy.Parameter(
            name="asset_tag",
            displayName="Specify the asset tag",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        params = [param0, param1, param2, param3, param4, param5]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        project_id = parameters[0].valueAsText
        # List buckets, folders and files
        if project_id:
            # Initialize a Cloud Storage client, for only once
            if not hasattr(self, "storage_client"):
                self.storage_client = storage.Client(project=project_id)

            # Get the list of all bucket names in this project
            buckets = self.storage_client.list_buckets()
            bucket_names = []
            for bucket in buckets:
                bucket_names.append(bucket.name)
            # Add bucket names to filter list
            parameters[1].filter.list = bucket_names

            # When bucket name is selected, list all available folders
            if parameters[1].valueAsText:
                bucket_name = parameters[1].valueAsText
                parameters[2].filter.list = list_folders_recursive(
                    self.storage_client, bucket_name
                )

            # When both bucket name and folder are selected, list all files
            if parameters[1].valueAsText and parameters[2].valueAsText:
                bucket_name = parameters[1].valueAsText
                folder_name = parameters[2].valueAsText
                # only certain formats are accepted as earth engine asset
                extensions = ("tif", "shp", "csv", "zip", "tfrecord")
                file_list = list_files_in_folder(
                    self.storage_client, bucket_name, folder_name
                )
                parameters[3].filter.list = [
                    file for file in file_list if file.endswith(extensions)
                ]

            # give a default asset path when project ID is provided
            if not parameters[5].valueAsText:
                parameters[5].value = "projects/" + project_id + "/assets/"

        # reset bucket, folder and file lists and values
        if not project_id:
            parameters[1].filter.list = []
            parameters[2].filter.list = []
            parameters[3].filter.list = []
            parameters[1].value = None
            parameters[2].value = None
            parameters[3].value = None
            parameters[5].value = None

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

        if parameters[0].valueAsText:
            if parameters[1].valueAsText:
                if not parameters[2].filter.list:
                    parameters[3].setWarningMessage("No folders found in this bucket.")
            # When both bucket name and folder are selected
            if parameters[1].valueAsText and parameters[2].valueAsText:
                if not parameters[3].filter.list:
                    parameters[3].setWarningMessage("No files found in this folder.")

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Read input parameters
        project_id = parameters[0].valueAsText
        bucket_name = parameters[1].valueAsText
        files = parameters[3].valueAsText
        asset_type = parameters[4].valueAsText
        asset_id = parameters[5].valueAsText

        # create storage client since self.storage_client can not transfer from updateParameters here
        self.storage_client = storage.Client(project=project_id)

        # Get the list of selected files
        # Remove ' in files in case users add it
        if "'" in files:
            files = files.replace("'", "")
        file_list = files.split(";")

        # If more than one file is selected, treat as collection asset
        is_col = False
        if len(file_list) > 1:
            is_col = True
            # use input asset id as folder path
            collection_asset_folder = asset_id
            # for image asset type, create image collection
            if asset_type == "image":
                if not asset_exists(collection_asset_folder):
                    create_image_collection(collection_asset_folder)
                else:
                    arcpy.AddMessage("The image collection already exists.")
            # if table, create a folder, all files will be uploaded to this folder
            else:
                if not asset_exists(collection_asset_folder):
                    create_ee_folder(collection_asset_folder)
                else:
                    arcpy.AddMessage("The folder already exists.")

        for ifile in file_list:
            # get file URI (file could be URI or relative path)
            if "gs://" not in ifile:
                bucket_uri = "gs://" + bucket_name + "/" + ifile
            else:
                bucket_uri = ifile
            # check if collection
            if is_col:
                # upload to collection folder
                # use file name as item id
                file_name = os.path.splitext(os.path.basename(bucket_uri))[0]
                item_id = f"{collection_asset_folder}/{file_name}"
                gcs_file_to_ee_asset(asset_type, item_id, bucket_uri)
            else:
                gcs_file_to_ee_asset(asset_type, asset_id, bucket_uri)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


""" Data Processing Tools """


# Apply Filters to GEE Object
class ApplyFilter:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Apply Filters to GEE Datasets"
        self.description = ""
        self.category = "Data Processing Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="data_type",
            displayName="Choose the type of the dataset to be filtered",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param0.filter.list = ["FeatureCollection", "ImageCollection"]

        param1 = arcpy.Parameter(
            name="asset_tag",
            displayName="Specify the asset tag of the dataset",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="filter_list",
            displayName="Specify the filters",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )
        param2.columns = [
            ["GPString", "Filters"],
            ["GPString", "Arguments"],
        ]
        # all filters in the ee.Filter
        filters = [
            "ee.Filter.and",  # Combines two or more filters with logical AND
            "ee.Filter.area",
            "ee.Filter.aside",
            "ee.Filter.bounds",  # Filter by geographic bounds (within a geometry)
            "ee.Filter.calendarRange",  # Filter by calendar range (e.g., specific years, months, days)
            "ee.Filter.contains",  # Checks if a collection contains a specific value
            "ee.Filter.date",  # Filter by date range
            "ee.Filter.daterangeContains",
            "ee.Filter.dayofYear",
            "ee.Filter.disjoint",
            "ee.Filter.eq",  # Equality filter (equals)
            "ee.Filter.equals",
            "ee.Filter.evaluate",
            "ee.Filter.expression",
            "ee.Filter.getInfo",
            "ee.Filter.greaterThan",
            "ee.Filter.greaterThanOrEuqals",
            "ee.Filter.gt",  # Greater than filter
            "ee.Filter.gte",  # Greater than or equal to filter
            "ee.Filter.hasType",
            "ee.Filter.inList",  # Filter by values within a list (like SQL's IN clause)
            "ee.Filter.intersects",  # Filter features that intersect a geometry
            "ee.Filter.isContained",  # Checks if a geometry is contained by another geometry
            "ee.Filter.lessThan",
            "ee.Filter.lessThanOrEquals",
            "ee.Filter.listContains",  # Filter if a list contains a specific value
            "ee.Filter.lt",  # Less than filter
            "ee.Filter.lte",  # Less than or equal to filter
            "ee.Filter.maxDifference",
            "ee.Filter.neq",  # Not equal filter
            "ee.Filter.not",  # Negates a filter
            "ee.Filter.notEuqals",
            "ee.Filter.notNull",  # Filters features where a property is not null
            "ee.Filter.or",  # Combines two or more filters with logical OR
            "ee.Filter.rangeContains",
            "ee.Filter.serialize",
            "ee.Filter.stringContains",  # Checks if a string contains a substring
            "ee.Filter.stringEndsWith",  # Checks if a string ends with a specific substring
            "ee.Filter.stringStartsWith",  # Checks if a string starts with a specific substring
            "ee.Filter.withinDistance",
        ]
        param2.filters[0].list = filters

        param3 = arcpy.Parameter(
            name="out_json",
            displayName="Specify the output JSON file to save the string format of the filtered dataset",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Read input parameters
        data_type = parameters[0].valueAsText
        asset_tag = parameters[1].valueAsText
        filters = parameters[2].values
        out_json = parameters[3].valueAsText

        # Retrieve the Earth Engine object based on the asset tag and data type
        if data_type == "FeatureCollection":
            ee_object = ee.FeatureCollection(asset_tag)
        elif data_type == "Image":
            ee_object = ee.Image(asset_tag)
        elif data_type == "ImageCollection":
            ee_object = ee.ImageCollection(asset_tag)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        # Apply the filters from the filter list to the Earth Engine object
        for filter_item in filters:
            filter_type = filter_item[0]
            filter_arg = filter_item[1]

            # Construct a command string based on the filter type
            command_string = f"{filter_type}({filter_arg})"
            constructed_filter = eval(command_string)
            ee_object = ee_object.filter(constructed_filter)

        # Serialize the filtered Earth Engine object to a string
        # serialized_object = ee_object.serialize()

        # Save the serialized string as JSON to the specified output path
        if not out_json.endswith(".json"):
            out_json = out_json + ".json"

        # use Kel's code
        arcgee.data.save_ee_result(ee_object, out_json)

        # with open(out_json, "w") as f:
        #    json.dump({"ee_object": serialized_object}, f)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Apply Reducers to GEE Object
class ApplyReducer:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Apply Reducers to GEE Datasets"
        self.description = ""
        self.category = "Data Processing Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="data_type",
            displayName="Choose the type of the dataset to be filtered",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param0.filter.list = ["FeatureCollection", "Image", "ImageCollection"]

        param1 = arcpy.Parameter(
            name="reducer_type",
            displayName="Choose the type of reducer",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="asset_tag",
            displayName="Specify the asset tag of the dataset",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param3 = arcpy.Parameter(
            name="reducer_list",
            displayName="Specify the reducers",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )
        param3.columns = [
            ["GPString", "Filters"],
            ["GPString", "Arguments"],
        ]
        # all reducers in ee.Reducer
        reducers = [
            "ee.Reducer.allNonZero",
            "ee.Reducer.anyNonZero",
            "ee.Reducer.autoHistogram",
            "ee.Reducer.bitwiseAnd",
            "ee.Reducer.bitwiseOr",
            "ee.Reducer.centeredCovariance",
            "ee.Reducer.circularMean",
            "ee.Reducer.circularStddev",
            "ee.Reducer.circularVariance",
            "ee.Reducer.combine",
            "ee.Reducer.count",
            "ee.Reducer.countDistinct",
            "ee.Reducer.countDistinctNonNull",
            "ee.Reducer.countEvery",
            "ee.Reducer.countRuns",
            "ee.Reducer.covariance",
            "ee.Reducer.disaggregate",
            "ee.Reducer.first",
            "ee.Reducer.firstNonNull",
            "ee.Reducer.fixed2DHistogram",
            "ee.Reducer.fixedHistogram",
            "ee.Reducer.forEach",
            "ee.Reducer.forEachBand",
            "ee.Reducer.frequencyHistogram",
            "ee.Reducer.geometricMedian",
            "ee.Reducer.getOutputs",
            "ee.Reducer.group",
            "ee.Reducer.histogram",
            "ee.Reducer.intervalMean",
            "ee.Reducer.kendallsCorrelation",
            "ee.Reducer.kurtosis",
            "ee.Reducer.last",
            "ee.Reducer.lastNonNull",
            "ee.Reducer.linearFit",
            "ee.Reducer.linearRegression",
            "ee.Reducer.max",
            "ee.Reducer.mean",
            "ee.Reducer.median",
            "ee.Reducer.min",
            "ee.Reducer.minMax",
            "ee.Reducer.mode",
            "ee.Reducer.pearsonsCorrelation",
            "ee.Reducer.percentile",
            "ee.Reducer.product",
            "ee.Reducer.repeat",
            "ee.Reducer.ridgeRegression",
            "ee.Reducer.robustLinearRegression",
            "ee.Reducer.sampleStdDev",
            "ee.Reducer.sampleVariance",
            "ee.Reducer.sensSlope",
            "ee.Reducer.setOutputs",
            "ee.Reducer.skew",
            "ee.Reducer.spearmansCorrelation",
            "ee.Reducer.splitWeigths",
            "ee.Reducer.stdDev",
            "ee.Reducer.sum",
            "ee.Reducer.toCollection",
            "ee.Reducer.toList",
            "ee.Reducer.unweighted",
            "ee.Reducer.variance",
        ]
        param3.filters[0].list = reducers

        param4 = arcpy.Parameter(
            name="out_json",
            displayName="Specify the output JSON file to save the string format of the filtered dataset",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        data_type = parameters[0].valueAsText
        if data_type == "FeatureCollection":
            parameters[1].filter.list = ["reduceColumns", "reduceToImage"]
        elif data_type == "Image":
            parameters[1].filter.list = [
                "reduce",
                "reduceConnectedComponents",
                "reduceNeighborhood",
                "reduceRegion",
                "reduceRegions",
                "reduceResolution",
                "reduceToVectors",
            ]
        elif data_type == "ImageCollection":
            parameters[1].filter.list = ["reduce", "reduceColumns", "reduceToImage"]
        else:
            parameters[1].filter.list = []

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Read input parameters
        data_type = parameters[0].valueAsText
        asset_tag = parameters[1].valueAsText
        filters = parameters[2].values
        out_json = parameters[3].valueAsText

        # Retrieve the Earth Engine object based on the asset tag and data type
        if data_type == "FeatureCollection":
            ee_object = ee.FeatureCollection(asset_tag)
        elif data_type == "Image":
            ee_object = ee.Image(asset_tag)
        elif data_type == "ImageCollection":
            ee_object = ee.ImageCollection(asset_tag)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        # Apply the filters from the filter list to the Earth Engine object
        for filter_item in filters:
            filter_type = filter_item[0]
            filter_arg = filter_item[1]

            # Construct a command string based on the filter type
            command_string = f"{filter_type}({filter_arg})"
            constructed_filter = eval(command_string)
            ee_object = ee_object.filter(constructed_filter)

        # Serialize the filtered Earth Engine object to a string
        serialized_object = ee_object.serialize()

        # Save the serialized string as JSON to the specified output path
        if not out_json.endswith(".json"):
            out_json = out_json + ".json"

        with open(out_json, "w") as f:
            json.dump({"ee_object": serialized_object}, f)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Apply Map Functions to Image Collection or Feature Collection
class ApplyMapFunction:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Apply Map Functions to GEE Datasets"
        self.description = ""
        self.category = "Data Processing Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="data_type",
            displayName="Choose the type of the dataset to be filtered",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param0.filter.list = ["FeatureCollection", "ImageCollection"]

        param1 = arcpy.Parameter(
            name="asset_tag",
            displayName="Specify the asset tag of the dataset",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )

        param2 = arcpy.Parameter(
            name="map_file",
            displayName="Select the Python script that contains map functions",
            datatype="DEFile",
            direction="Input",
            multiValue=False,
            parameterType="Required",
        )
        param2.filter.list = ["py"]

        param3 = arcpy.Parameter(
            name="map_functions",
            displayName="Select the map functions to apply",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required",
        )

        param4 = arcpy.Parameter(
            name="out_json",
            displayName="Specify the output JSON file to save the string format of the filtered dataset",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # List all functions in the imported module
        def list_functions_from_script(module):
            function_list = []
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj):
                    function_list.append(name)
            return function_list

        import inspect
        import importlib

        # When the map function file is selected
        if parameters[2].valueAsText:
            # get the file name of input map function file
            file_path = parameters[2].valueAsText
            map_lib = os.path.splitext(os.path.basename(file_path))[0]
            module = importlib.import_module(map_lib)

            function_list = list_functions_from_script(module)
            parameters[3].filter.list = function_list

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        import importlib

        # Read input parameters
        data_type = parameters[0].valueAsText
        asset_tag = parameters[1].valueAsText
        map_file = parameters[2].valueAsText
        map_functions = parameters[3].valueAsText
        out_json = parameters[4].valueAsText

        # get list of map functions
        if "'" in map_functions:
            map_functions = map_functions.replace("'", "")
        function_list = map_functions.split(";")

        # import module first
        map_lib = os.path.splitext(os.path.basename(map_file))[0]
        module = importlib.import_module(map_lib)

        # Retrieve the Earth Engine object based on the asset tag and data type
        if data_type == "FeatureCollection":
            ee_object = ee.FeatureCollection(asset_tag)
        elif data_type == "ImageCollection":
            ee_object = ee.ImageCollection(asset_tag)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        # Apply the filters from the filter list to the Earth Engine object
        for func_str in function_list:
            function_to_call = getattr(module, func_str)
            ee_object = ee_object.map(function_to_call)

        # Serialize the filtered Earth Engine object to a string
        serialized_object = ee_object.serialize()

        # Save the serialized string as JSON to the specified output path
        if not out_json.endswith(".json"):
            out_json = out_json + ".json"

        with open(out_json, "w") as f:
            json.dump({"ee_object": serialized_object}, f)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Run User-Provided Python Script
class RunPythonScript:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Run User-Provided Python Script"
        self.description = ""
        self.category = "Data Processing Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="py_script",
            displayName="Choose the python script to run",
            datatype="DEFile",
            direction="Input",
            parameterType="Required",
        )
        param0.filter.list = ["py"]

        params = [param0]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        import subprocess

        # Read input parameters
        py_script = parameters[0].valueAsText

        # Run the script as an external process
        subprocess.run(["python", py_script])

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Run Earth Engine Operation
class EEOpTool:
    def __init__(self):
        self.label = "EE Operation"
        self.description = "Tool to run arbitrary Earth Engine operation"
        self.category = "Data Processing Tools"
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        project_id = arcpy.Parameter(
            displayName="Cloud Project ID",
            name="project_id",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        ee_method = arcpy.Parameter(
            displayName="EE Method call",
            name="ee_method",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        in_value = arcpy.Parameter(
            displayName="Input EE Value",
            name="in_value",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        in_args = arcpy.Parameter(
            displayName="Input Arguments",
            name="in_args",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True,
        )

        in_kwargs = arcpy.Parameter(
            displayName="Input Keywords",
            name="in_kwargs",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True,
        )
        # Defines the structure of the input table
        in_kwargs.columns = [
            ["GPString", "Keyword Name"],
            ["GPString", "Value"],
            ["GPString", "Type"],
        ]

        out_value = arcpy.Parameter(
            displayName="Output EE Value",
            name="out_value",
            datatype="GPString",
            parameterType="Required",
            direction="Output",
        )

        params = [project_id, ee_method, in_value, in_args, in_kwargs, out_value]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        # TODO(kmarkert): check if EE is initialized and then
        # not sure how auth may be handeled with model builder chain...
        arcgee.data.auth(project=parameters[0].valueAsText)

        in_ee_obj = arcgee.data.load_ee_result(parameters[2].valueAsText)

        ee_method_str = parameters[1].valueAsText

        if ee_method_str.startswith("ee."):
            ee_method_str = ee_method_str.replace("ee.", "")

        ee_cls, ee_call = ee_method_str.split(".")
        ee_method = getattr(getattr(ee, ee_cls), ee_call)

        # need to parse and verify input args to the correct type...
        args_ = parameters[3].valueAsText
        if args_ is not None:
            args = [eval(element.strip()) for element in args_.split(";")]
            for arg in args:
                messages.addMessage(f"{arg}: {type(arg)}")
        else:
            args = []

        # TODO(kmarkert) update the parsing of kwargs
        in_kwargs_ = parameters[4].valueAsText
        messages.addMessage(in_kwargs_)
        kwargs = {}
        # if in_kwargs_ is not None and ';' in in_kwargs_:
        #     in_kwargs = in_kwargs_.split(';')

        #     if len(kwargs) > 1:
        #         for element in in_kwargs:
        #             key, value, t = element.split(' ')
        #             if 'ee' not in t:
        #                 kwargs[key] = eval(f'{t}({value})')
        #             elif 'ee' in t:
        #                 v = arcgee.data.load_ee_result(value)
        #                 kwargs[key] = v
        if in_kwargs_ is not None:
            key, value, t = in_kwargs_.split(" ")
            if "ee" not in t:
                kwargs[key] = eval(value)
            elif "ee" in t:
                v = arcgee.data.load_ee_result(value)
                kwargs[key] = v

        messages.addMessage(f"{kwargs}")

        # set up requet to Earth Engine
        ee_result = ee_method(in_ee_obj, *args, **kwargs)

        out_path = parameters[5].valueAsText

        arcgee.data.save_ee_result(ee_result, out_path)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


########################################################
################### Not in Use #########################
########################################################
# Add GEE Asset Object to ArcGIS map
class EEMapTool:
    def __init__(self):
        self.label = "Add EE to Map"
        self.description = "Add Serialized GEE Object to Map"

    def getParameterInfo(self):
        """Define the tool parameters."""

        project_id = arcpy.Parameter(
            displayName="Cloud Project ID",
            name="project_id",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        in_value = arcpy.Parameter(
            displayName="Input EE Value",
            name="in_value",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )

        vis_params = arcpy.Parameter(
            displayName="Visualization Parameters",
            name="vis_param",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True,
        )
        vis_params.columns = [["GPString", "Parameter"], ["GPString", "Value"]]

        layer_name = arcpy.Parameter(
            displayName="Layer Name",
            name="layer_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )

        params = [project_id, in_value, vis_params, layer_name]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        # TODO(kmarkert): check if EE is initialized and then
        # not sure how auth may be handeled with model builder chain...
        arcgee.data.auth(project=parameters[0].valueAsText)

        in_ee_obj = arcgee.data.load_ee_result(parameters[1].valueAsText)

        in_vis_ = parameters[2].valueAsText
        if in_vis_ is not None:
            in_vis = in_vis_.split(";")
            vis_params = {}
            for element in in_vis:
                key, value = element.split(" ")
                for t in [int, float]:
                    try:
                        value = t(value)
                    except:
                        pass

                vis_params[key] = value
        else:
            vis_params = None

        layer_name = parameters[3].valueAsText

        arcgee.map.add_layer(in_ee_obj, vis_params, layer_name)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Add GEE Image to Map
class AddImage2Map:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add GEE Image to Map"
        self.description = ""
        self.category = ""
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="asset_tag",
            displayName="Specify GEE Asset Tag",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param0.dialogref = "Browse all available datasets from GEE website, copy and paste the asset tag here."

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Specify three bands for RGB visualization",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param3 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="gamma",
            displayName="Specify gamma correction factors",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional",
        )

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Check band list of a given asset
        asset_tag = parameters[0].valueAsText
        if asset_tag:
            image = ee.Image(asset_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display
            band_res_list = []
            for iband in band_list:
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + "--" + str(round(res)) + "--m")

            parameters[1].filter.list = band_res_list

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        img_label = parameters[0].valueAsText
        band_str = parameters[1].valueAsText
        min_val = parameters[2].valueAsText
        max_val = parameters[3].valueAsText
        gamma_str = parameters[4].valueAsText
        palette_str = parameters[5].valueAsText

        # Define visualization parameters
        vis_params = {}

        # Add bands to vis_params if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            vis_params["bands"] = bands_only

        # Add min and max values if specified
        if min_val:
            vis_params["min"] = float(min_val)
        if max_val:
            vis_params["max"] = float(max_val)

        # Add gamma correction factors if specified
        if gamma_str:
            # Remove ' in gamma string in case users add it
            if "'" in gamma_str:
                gamma_str = gamma_str.replace("'", "")
            gamma = [float(item) for item in gamma_str.split(",")]
            vis_params["gamma"] = gamma

        # Add color palette if specified
        if palette_str:
            # arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str:
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified
            palette = palette_str.split(",")
            # arcpy.AddMessage(palette)
            vis_params["palette"] = palette

        # Get image by label
        dem = ee.Image(img_label)
        # Get the map ID and token
        map_id_dict = dem.getMapId(vis_params)

        # Construct the URL
        map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

        # Add map URL to the current ArcMap
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.listMaps("Map")[0]
        tsl = aprxMap.addDataFromPath(map_url)
        # Add band information to map name
        if band_str:
            tsl.name = img_label + "--" + "--".join(bands_only)
        else:
            tsl.name = img_label

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download GEE Image by GetDownloadURL Max. 48MB
class DownloadSmallImage:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download GEE Image in Small Chunk (Maximum 48MB)"
        self.description = ""
        self.category = ""
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="asset_tag",
            displayName="Specify GEE Image Asset Tag",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param0.dialogref = ""

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Specify the Bands for Download",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="scale",
            displayName="Specify the Scale for Download",
            datatype="GPDouble",
            direction="Input",
            multiValue=False,
            parameterType="Optional",
        )

        param3 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a Polygon or Polyline as Region of Interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="use_extent",
            displayName="Use current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param5 = arcpy.Parameter(
            name="out_tiff",
            displayName="Specify the Output File Name",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Check band list of a given asset
        # Only update filter list once to avoid extra computation
        asset_tag = parameters[0].valueAsText
        if asset_tag and not parameters[1].filter.list:
            image = ee.Image(asset_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display
            band_res_list = []
            for iband in band_list:
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + "--" + str(round(res)) + "--m")

            parameters[1].filter.list = band_res_list

        # Capture the suggested scale value based on selected bands
        band_str = parameters[1].valueAsText
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            scale_only = [float(iband.split("--")[1]) for iband in bands]
            parameters[2].value = max(scale_only)

        # Disable input feature if map extent is used
        if parameters[4].value:  # map extent selected
            parameters[3].enabled = False
        else:
            parameters[3].enabled = True

        # Reset band filter list when asset tag is empty
        if not asset_tag:
            parameters[1].filter.list = []

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        asset_tag = parameters[0].valueAsText
        band_str = parameters[1].valueAsText
        scale = parameters[2].valueAsText
        in_poly = parameters[3].valueAsText
        use_extent = parameters[4].valueAsText
        out_tiff = parameters[5].valueAsText

        # Define a function to project a point to WGS 84 (EPSG 4326)
        def project_to_wgs84(x, y, in_spatial_ref):
            point = arcpy.Point(x, y)
            point_geom = arcpy.PointGeometry(point, in_spatial_ref)
            wgs84 = arcpy.SpatialReference(4326)
            point_geom_wgs84 = point_geom.projectAs(wgs84)
            return point_geom_wgs84.centroid.X, point_geom_wgs84.centroid.Y

        # Initialize parameters for getDownloadURL
        params_dict = {}

        # Add bands to vis_params if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            params_dict["bands"] = bands_only

        # Make sure output file name ends with .tif
        if not out_tiff.endswith(".tif"):
            out_tiff = out_tiff + ".tif"

        # Check GEE image projection
        image = ee.Image(asset_tag)
        # CRS could be other projections than 'EPSG:4326' for some GEE assets
        # When multiple band, select one for projection
        img_prj = image.select(0).projection().crs().getInfo()
        arcpy.AddMessage("Image projection is " + img_prj)

        # Get the region of interests
        # Use map view extent if checked
        if use_extent == "true":
            xmin, ymin, xmax, ymax = get_map_view_extent()
            roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)

        # Use input feature layer as ROI
        else:
            spatial_ref = arcpy.Describe(in_poly).spatialReference
            poly_prj = spatial_ref.PCSCode
            arcpy.AddMessage("Input feature layer projection is " + str(poly_prj))

            # Project input feature to GEE image coordinate system if needed
            target_poly = in_poly
            if str(poly_prj) not in img_prj:
                arcpy.AddMessage(
                    "Projecting input feature layer to GEE image cooridnate system ..."
                )
                out_sr = arcpy.SpatialReference(int(img_prj.split(":")[1]))
                arcpy.Project_management(in_poly, "poly_temp", out_sr)
                target_poly = "poly_temp"

            # convert input feature to geojson
            arcpy.FeaturesToJSON_conversion(
                target_poly, "temp.geojson", "FORMATTED", "", "", "GEOJSON"
            )

            # Read the GeoJSON file
            upper_path = os.path.dirname(arcpy.env.workspace)
            file_geojson = os.path.join(upper_path, "temp.geojson")
            with open(file_geojson) as f:
                geojson_data = json.load(f)

            # Collect polygon object coordinates
            coords = []
            for feature in geojson_data["features"]:
                coords.append(feature["geometry"]["coordinates"])
            arcpy.AddMessage("Total number of polygon objects: " + str(len(coords)))

            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)
            # Delete temporary geojson
            arcpy.management.Delete(file_geojson)

        # Clip image to ROI only
        image = image.clip(roi)

        params_dict["region"] = roi  # The region to clip and download
        if scale:
            params_dict["scale"] = float(scale)  # Resolution in meters per pixel
        params_dict["format"] = "GEO_TIFF"  # The file format of the downloaded image

        # Specify the download parameters
        download_url = image.getDownloadURL(params_dict)

        arcpy.AddMessage("Download URL is: " + download_url)
        arcpy.AddMessage("Downloading to " + out_tiff + " ...")

        response = requests.get(download_url)
        with open(out_tiff, "wb") as fd:
            fd.write(response.content)

        arcpy.AddMessage(out_tiff)

        # Add out tiff to map layer
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.activeMap
        aprxMap.addDataFromPath(out_tiff)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return


# Download by Getting Pixels, Max. 3 Bands and 48MB
class DownloadImagePixels:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download GEE Image by Pixels (Maximum 3 Bands and 48MB)"
        self.description = ""
        self.category = ""
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            name="asset_tag",
            displayName="Specify GEE Image Asset Tag",
            datatype="GPString",
            direction="Input",
            parameterType="Required",
        )
        param0.dialogref = ""

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Specify the Bands for Download",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Optional",
        )

        param2 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a Polygon or Polyline as Region of Interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional",
        )

        param3 = arcpy.Parameter(
            name="use_extent",
            displayName="Use current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional",
        )

        param4 = arcpy.Parameter(
            name="out_tiff",
            displayName="Specify the Output File Name",
            datatype="DEFile",
            direction="Output",
            parameterType="Required",
        )

        params = [param0, param1, param2, param3, param4]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Check band list of a given asset
        # Only update filter list once to avoid extra computation
        asset_tag = parameters[0].valueAsText
        if asset_tag and not parameters[1].filter.list:
            image = ee.Image(asset_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display
            band_res_list = []
            for iband in band_list:
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + "--" + str(round(res)) + "--m")

            parameters[1].filter.list = band_res_list

        # Disable input feature if map extent is used
        if parameters[3].value:
            parameters[2].enabled = False
        else:
            parameters[2].enabled = True

        # Reset band filter list when asset tag is empty
        if not asset_tag:
            parameters[1].filter.list = []

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

        # Make sure maximum 3 bands selected
        band_str = parameters[1].valueAsText
        if band_str:
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            if len(bands) > 3:
                parameters[1].setErrorMessage("You can only select up to 3 bands.")
            else:
                parameters[1].clearMessage()

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        asset_tag = parameters[0].valueAsText
        band_str = parameters[1].valueAsText
        in_poly = parameters[2].valueAsText
        use_extent = parameters[3].valueAsText
        out_tiff = parameters[4].valueAsText

        # Define a function to project a point to WGS 84 (EPSG 4326)
        def project_to_wgs84(x, y, in_spatial_ref):
            point = arcpy.Point(x, y)
            point_geom = arcpy.PointGeometry(point, in_spatial_ref)
            wgs84 = arcpy.SpatialReference(4326)
            point_geom_wgs84 = point_geom.projectAs(wgs84)
            return point_geom_wgs84.centroid.X, point_geom_wgs84.centroid.Y

        # Convert BBox to Polygon
        def bbox_to_polygon(in_bbox):
            # Get the coordinates from the BBox
            coords = in_bbox.coordinates().getInfo()
            # Create the ee.Geometry.Polygon
            out_poly = ee.Geometry.Polygon(coords)
            return out_poly

        # Initialize parameters for getDownloadURL
        params_dict = {}
        params_dict["fileFormat"] = "GEO_TIFF"
        params_dict["assetId"] = asset_tag

        # Add bands to vis_params if specfied
        if band_str:
            # Remove ' in band string in case users add it
            if "'" in band_str:
                band_str = band_str.replace("'", "")
            bands = band_str.split(";")
            bands_only = [iband.split("--")[0] for iband in bands]
            params_dict["bandIds"] = bands_only

        # Make sure output file name ends with .tif
        if not out_tiff.endswith(".tif"):
            out_tiff = out_tiff + ".tif"

        # Check GEE image projection
        image = ee.Image(asset_tag)
        # CRS could be other projections than 'EPSG:4326' for some GEE assets
        # When multiple band, select one for projection
        img_prj = image.select(0).projection().crs().getInfo()
        arcpy.AddMessage("Image projection is " + img_prj)

        # Get the region of interests
        # Use map view extent if checked
        if use_extent == "true":
            xmin, ymin, xmax, ymax = get_map_view_extent()
            bbox = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
            roi = bbox_to_polygon(bbox)
        # Use input feature layer as ROI
        else:
            spatial_ref = arcpy.Describe(in_poly).spatialReference
            poly_prj = spatial_ref.PCSCode
            arcpy.AddMessage("Input feature layer projection is " + str(poly_prj))

            # Project input feature to GEE image coordinate system if needed
            target_poly = in_poly
            if str(poly_prj) not in img_prj:
                arcpy.AddMessage(
                    "Projecting input feature layer to GEE image cooridnate system ..."
                )
                out_sr = arcpy.SpatialReference(int(img_prj.split(":")[1]))
                arcpy.Project_management(in_poly, "poly_temp", out_sr)
                target_poly = "poly_temp"

            # convert input feature to geojson
            arcpy.FeaturesToJSON_conversion(
                target_poly, "temp.geojson", "FORMATTED", "", "", "GEOJSON"
            )

            # Read the GeoJSON file
            upper_path = os.path.dirname(arcpy.env.workspace)
            file_geojson = os.path.join(upper_path, "temp.geojson")
            with open(file_geojson) as f:
                geojson_data = json.load(f)

            # Collect polygon object coordinates
            coords = []
            for feature in geojson_data["features"]:
                coords.append(feature["geometry"]["coordinates"])
            arcpy.AddMessage("Total number of polygon objects: " + str(len(coords)))

            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)
            # Delete temporary geojson
            arcpy.management.Delete(file_geojson)

        params_dict["region"] = roi.toGeoJSON()

        # arcpy.AddMessage(roi.toGeoJSON())

        # Clip image to ROI only
        # image = image.clip(multi_polygon)

        # Use ee.data.getPixels to get the pixel data
        pixels = ee.data.getPixels(params_dict)

        # Save the pixel data to a file
        with open(out_tiff, "wb") as f:
            f.write(pixels)

        arcpy.AddMessage("Saving file to path: " + out_tiff)
        # Add out tiff to map layer
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.activeMap
        aprxMap.addDataFromPath(out_tiff)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
