# -*- coding: utf-8 -*-

import arcpy
import ee
import os
import json
import requests
import numpy as np
import xarray
import rasterio
from rasterio.transform import from_origin

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        tools = []
        tools.append(GEEAuth)
        #tools.append(AddImage2Map)
        tools.append(AddImgCol2Map)
        tools.append(AddFeatCol2Map)
        #tools.append(DownloadSmallImage)
        #tools.append(DownloadImagePixels)
        tools.append(DownloadLargeImage)
        
        self.tools = tools

# GEE Authentication
class GEEAuth:
    
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "GEE Authentication"
        self.description = ""
        self.category = ""
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="json_key",
            displayName="Choose the JSON key file of the target Google Cloud project",
            datatype="DEFile",
            direction="Input",
            parameterType="Optional")
        
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

        # Read input parameters 
        json_key = parameters[0].valueAsText

        # Read JSON key file
        if json_key :
            arcpy.AddMessage(json_key)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json_key

        # Define functions
        def clear_credentials():
            credentials_path = os.path.expanduser("~/.config/earthengine/credentials")
            if os.path.exists(credentials_path):
                os.remove(credentials_path)
                arcpy.AddMessage("Previous credentials are removed. Re-authenticate now ...")
                
        def authenticate_earth_engine():
            try:
                ee.Authenticate()
                ee.Initialize()
                arcpy.AddMessage("Authentication successful")
            except Exception as e:
                arcpy.AddMessage(f"Authentication failed: {e}")    

        clear_credentials()
        authenticate_earth_engine()
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
            parameterType="Required")
        param0.dialogref = "Browse all available datasets from GEE website, copy and paste the asset tag here."

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Specify three bands for RGB visualization",
            datatype="GPString",
            direction="Input",
            multiValue=True, 
            parameterType="Optional")
        
        param2 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional")

        param3 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional")
        
        param4 = arcpy.Parameter(
            name="gamma",
            displayName="Specify gamma correction factors",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")
        
        param5 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")
        
        params = [param0,param1,param2,param3,param4, param5]
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
        if asset_tag :
            # Only initialize ee when asset tag is given 
            ee.Initialize()
            image = ee.Image(asset_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display 
            band_res_list = []
            for iband in band_list :
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + '--' + str(round(res))+'--m')
                
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
        if band_str :
            # Remove ' in band string in case users add it
            if "'" in band_str :
                band_str = band_str.replace("'","")
            bands = band_str.split(';')
            bands_only = [iband.split('--')[0] for iband in bands]
            vis_params['bands'] = bands_only

        # Add min and max values if specified 
        if min_val :
            vis_params['min'] = float(min_val)
        if max_val :
            vis_params['max'] = float(max_val)
        
        # Add gamma correction factors if specified
        if gamma_str :
            # Remove ' in gamma string in case users add it 
            if "'" in gamma_str :
                gamma_str = gamma_str.replace("'","")
            gamma = [float(item) for item in gamma_str.split(',')]
            vis_params['gamma'] = gamma 
        
        # Add color palette if specified 
        if palette_str :
            #arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str :
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified 
            palette = palette_str.split(',')
            #arcpy.AddMessage(palette)
            vis_params['palette'] = palette
        
        # Initialize GEE, initial project is saved in Gcloud application default login JSON
        ee.Initialize()
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
        if band_str :
            tsl.name = img_label + '--' + '--'.join(bands_only)
        else :
            tsl.name = img_label 
        
        
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

# Add GEE Image Collection to Map 
class AddImgCol2Map:
    
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add GEE Image Collection to Map"
        self.description = ""
        self.category = ""
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        
        param0 = arcpy.Parameter(
            name="asset_tag",
            displayName="Specify GEE Image Collection Tag",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")
        param0.dialogref = "Browse all available datasets from GEE website, copy and paste the asset tag here."

        param1 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input", 
            parameterType="Optional")
        param1.columns = [['GPString','Starting Date'],['GPString', 'Ending Date']] 
        param1.value = [['2014-03-01','2014-05-01']]

        param2 = arcpy.Parameter(
            name="filter_bounds",
            displayName="Filter by location in coordinates",
            datatype="GPValueTable",
            direction="Input", 
            parameterType="Optional")
        param2.columns = [['GPString','Longitude'],['GPString', 'Latitude']]

        param3 = arcpy.Parameter(
            name="use_centroid",
            displayName="Use the center of the current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional")

        param4 = arcpy.Parameter(
            name="images",
            displayName="Select images by image ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required")
                
        param5 = arcpy.Parameter(
            name="bands",
            displayName="Specify three bands for RGB visualization",
            datatype="GPString",
            direction="Input",
            multiValue=True, 
            parameterType="Optional")
        
        param6 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional")

        param7 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional")
        
        param8 = arcpy.Parameter(
            name="gamma",
            displayName="Specify gamma correction factors",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")
        
        param9 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")
        
        params = [param0,param1,param2,param3,param4,
                  param5,param6,param7,param8,param9]
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
        if parameters[1].valueAsText :
            val_list = parameters[1].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
        else :
            start_date = None
            end_date = None
            
        # Get the filter bounds
        if parameters[3].value :
            # Disable input coordinates if map extent is used
            parameters[2].enabled = False
            # Get the current project
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
            poly_prj = spatial_ref.PCSCode
            if poly_prj == 0 : # projected is not used, try geographic
                poly_prj = spatial_ref.GCSCode
            # Always using latitude and longtiude for ee.Geometry, ee will automatically transform
            if str(poly_prj) not in 'EPSG:4326' : 
                # Convert the extent corners to EPSG 4326
                xmin, ymin = project_to_wgs84(xmin, ymin, spatial_ref)
                xmax, ymax = project_to_wgs84(xmax, ymax, spatial_ref)
            # Get the centroid of map extent 
            lon = (xmin+xmax)/2
            lat = (ymin+ymax)/2
        else :
            parameters[2].enabled = True  
            if parameters[2].valueAsText :
                val_list = parameters[2].values
                lon = val_list[0][0]
                lat = val_list[0][1]
            else :
                lon = None
                lat = None

        # Check image list of a given collection asset 
        asset_tag = parameters[0].valueAsText

        # Image collection size could be huge, may take long to load without filters
        # Only retrieve the list of images, when either filter dates or filter bounds are selected
        if asset_tag and ((start_date and end_date) or (lon and lat)):
            # Only initialize ee when asset tag is given 
            ee.Initialize()
            collection = ee.ImageCollection(asset_tag)
            # Filter image collection as specified
            if lon is not None and lat is not None :
                collection = collection.filterBounds(ee.Geometry.Point((float(lon), float(lat))))
            if start_date is not None and end_date is not None  :
                collection = collection.filterDate(start_date, end_date)
            # Get image IDs from collection
            image_ids = collection.aggregate_array('system:index').getInfo()
            parameters[4].filter.list = image_ids

        # Check band list of the selected image  
        img_id = parameters[4].valueAsText
        # Update only when filter list is empty 
        if img_id and not parameters[5].filter.list :
            # Only initialize ee when asset tag is given 
            ee.Initialize()
            if asset_tag :
                img_tag = asset_tag + '/' + img_id
            else :
                img_tag = img_id 
            image = ee.Image(img_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display 
            band_res_list = []
            for iband in band_list :
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + '--' + str(round(res))+'--m')
            parameters[5].filter.list = band_res_list

        # Reset band filter list when asset tag changes 
        if (not img_id) and (not parameters[0].valueAsText)  :
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
        #filter_dates = parameters[1].valueAsText
        #filter_bounds = parameters[2].valueAsText
        #use_extent = parameters[3].valueAsText
        img_id = parameters[4].valueAsText
        band_str = parameters[5].valueAsText
        min_val = parameters[6].valueAsText
        max_val = parameters[7].valueAsText
        gamma_str = parameters[8].valueAsText
        palette_str = parameters[9].valueAsText

        # Construct asset tag for selected image
        if asset_tag :
            img_tag = asset_tag + '/' + img_id
        else :
            img_tag = img_id 

        # Define visualization parameters
        vis_params = {}

        # Add bands to vis_params if specfied 
        if band_str :
            # Remove ' in band string in case users add it
            if "'" in band_str :
                band_str = band_str.replace("'","")
            bands = band_str.split(';')
            bands_only = [iband.split('--')[0] for iband in bands]
            # Ignore the resolution part 
            vis_params['bands'] = bands_only

        # Add min and max values if specified 
        if min_val :
            vis_params['min'] = float(min_val)
        if max_val :
            vis_params['max'] = float(max_val)
        
        # Add gamma correction factors if specified
        if gamma_str :
            # Remove ' in gamma string in case users add it 
            if "'" in gamma_str :
                gamma_str = gamma_str.replace("'","")
            gamma = [float(item) for item in gamma_str.split(',')]
            vis_params['gamma'] = gamma 
        
        # Add color palette if specified 
        if palette_str :
            #arcpy.AddMessage(palette_str)
            # Remove ' in palette string in case users add it
            if "'" in palette_str :
                palette_str = palette_str.replace("'", "")
            # Convert palette string to list if specified 
            palette = palette_str.split(',')
            #arcpy.AddMessage(palette)
            vis_params['palette'] = palette
        
        # Initialize GEE, initial project is saved in Gcloud application default login JSON
        ee.Initialize()
        # Get image by label  
        dem = ee.Image(img_tag)
        # Get the map ID and token
        map_id_dict = dem.getMapId(vis_params)

        # Construct the URL
        map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

        # Add map URL to the current ArcMap 
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.listMaps("Map")[0]
        tsl = aprxMap.addDataFromPath(map_url)
        # Add band information to map name 
        if band_str :
            tsl.name = img_tag + '--' + '--'.join(bands_only)
        else :
            tsl.name = img_tag  
        
        
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

# Add GEE Feature Collection to Map 
class AddFeatCol2Map:
    
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Add GEE Feature Collection to Map"
        self.description = ""
        self.category = ""
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
            displayName="Specify GEE Asset Tag",
            datatype="GPString",
            direction="Input",
            parameterType="Required")
        param0.dialogref = "Browse all available datasets from GEE website, copy and paste the asset tag here."

        param1 = arcpy.Parameter(
            name="filter_props",
            displayName="Filter by Properties",
            datatype="GPValueTable",
            direction="Input", 
            parameterType="Optional")
        param1.columns = [['GPString','Property Name'],['GPString', 'Filter Value']] 

        param2 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input", 
            parameterType="Optional")
        param2.columns = [['GPString','Starting Date'],['GPString', 'Ending Date']] 
        #param2.value = [['2014-03-01','2014-05-01']]

        param3 = arcpy.Parameter(
            name="filter_bounds",
            displayName="Filter by location in coordinates",
            datatype="GPValueTable",
            direction="Input", 
            parameterType="Optional")
        param3.columns = [['GPString','Longitude'],['GPString', 'Latitude']]

        param4 = arcpy.Parameter(
            name="use_centroid",
            displayName="Use the center of the current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional")
                        
        param5 = arcpy.Parameter(
            name="color",
            displayName="Specify the color for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")
        
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
    
        params = [param0,param1,param2,param3,param4,param5]
                  #,param2,param3,param4,param5,param6,param7]
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
        
        if parameters[0].valueAsText and not parameters[1].filters[0].list :
            asset_tag = parameters[0].valueAsText 
            ee.Initialize()
            fc = ee.FeatureCollection(asset_tag)
            prop_names = fc.first().propertyNames().getInfo()
            parameters[1].filters[0].list = sorted(prop_names)   

        # Reset filter list 
        if not parameters[0].valueAsText :
            parameters[1].filters[0].list = []

        # Disable input coordinates if map extent is used 
        if parameters[4].value :
            parameters[3].enabled = False
        else :
            parameters[3].enabled = True        

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

        # Make sure property name is only used once 
        prop_list = []
        if parameters[1].valueAsText :
            val_list = parameters[1].values
            for row in val_list :
                prop_name = row[0]
                if prop_name not in prop_list :
                    prop_list.append(prop_name)
                else :
                    parameters[1].setErrorMessage(f"The property name '{prop_name}' is used more than once. Please use unique property names.")
                    return

    def execute(self, parameters, messages):
        """
        The source code of the tool.
        """
        # Define a function to project a point to WGS 84 (EPSG 4326)
        def project_to_wgs84(x, y, in_spatial_ref):
            point = arcpy.Point(x, y)
            point_geom = arcpy.PointGeometry(point, in_spatial_ref)
            wgs84 = arcpy.SpatialReference(4326)
            point_geom_wgs84 = point_geom.projectAs(wgs84)
            return point_geom_wgs84.centroid.X, point_geom_wgs84.centroid.Y
        
        asset_tag  = parameters[0].valueAsText
        feat_color = parameters[2].valueAsText

        # point_shape= parameters[2].valueAsText
        # point_size = parameters[3].valueAsText
        # line_width = parameters[4].valueAsText
        # line_type  = parameters[5].valueAsText
        # fill_color = parameters[6].valueAsText
        # opacity    = parameters[7].valueAsText



        # Define visualization parameters
        vis_params = {}
        # Add color to vis_params if specified 
        if feat_color :
            vis_params['color'] = feat_color
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
        
        # Initialize GEE, initial project is saved in Gcloud application default login JSON
        ee.Initialize()
        # Get image by label  
        fc = ee.FeatureCollection(asset_tag)

        # Filter by properties
        if parameters[1].valueAsText :
            val_list = parameters[1].values
            # Could be multiple filter properties 
            for row in val_list :
                prop_name = row[0]
                # property value could be integer, float or string 
                try:
                    prop_val = int(row[1])
                except ValueError:
                    try:
                        prop_val = float(row[1])
                    except ValueError:
                        prop_val = row[1]

                # Check if prop_val is a string and format accordingly
                if isinstance(prop_val, str):
                    # If prop_val is a string, wrap it in single quotes
                    filter_condition = "{} == '{}'".format(prop_name, prop_val)
                else:
                    # If prop_val is an integer or float, no quotes needed
                    filter_condition = "{} == {}".format(prop_name, prop_val)

                arcpy.AddMessage('Filter by property: ' + filter_condition)
                fc = fc.filter(filter_condition)

        # Filter by dates if specified 
        if parameters[2].valueAsText :
            val_list = parameters[2].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
            fc = fc.filterDate(start_date, end_date)

        # Filter by bounds if specified 
        if parameters[4].value : # Use map extent
            # Get the current project
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
            poly_prj = spatial_ref.PCSCode
            if poly_prj == 0 :
                poly_prj = spatial_ref.GCSCode
            # Always using latitude and longtiude for ee.Geometry, ee will automatically transform
            if str(poly_prj) not in 'EPSG:4326' : 
                # Convert the extent corners to EPSG 4326
                xmin, ymin = project_to_wgs84(xmin, ymin, spatial_ref)
                xmax, ymax = project_to_wgs84(xmax, ymax, spatial_ref)
            # Get the centroid of map extent 
            lon = (xmin+xmax)/2
            lat = (ymin+ymax)/2
            fc = fc.filterBounds(ee.Geometry.Point((float(lon), float(lat))))
        else : # use input coordinates 
            if parameters[3].valueAsText :
                val_list = parameters[3].values
                lon = val_list[0][0]
                lat = val_list[0][1]
                fc = fc.filterBounds(ee.Geometry.Point((float(lon), float(lat))))
            else : # no filter by bounds 
                lon = None
                lat = None       

        # Feature collection could contain zero record after filters
        if fc.size().getInfo()>0 :
            # Get the map ID and token
            map_id_dict = fc.getMapId(vis_params)

            # Construct the URL
            map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

            # Add map URL to the current ArcMap 
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.listMaps("Map")[0]
            tsl = aprxMap.addDataFromPath(map_url)
            tsl.name = asset_tag 
        else :
            arcpy.AddWarning("No data record returned after applying filters! Please reset the filters and try again.")
                
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
            parameterType="Required")
        param0.dialogref = ""

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Specify the Bands for Download",
            datatype="GPString",
            direction="Input",
            multiValue=True, 
            parameterType="Optional")
        
        param2 = arcpy.Parameter(
            name="scale",
            displayName="Specify the Scale for Download",
            datatype="GPDouble",
            direction="Input",
            multiValue=False, 
            parameterType="Optional")        

        param3 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a Polygon or Polyline as Region of Interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional")
        
        param4 = arcpy.Parameter(
            name="use_extent",
            displayName="Use current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional")

        param5 = arcpy.Parameter(
            name="out_tiff",
            displayName="Specify the Output File Name",
            datatype="DEFile",
            direction="Output",
            parameterType="Required")
        
        params = [param0,param1,param2, param3, param4, param5]
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
            # Only initialize ee when asset tag is given 
            ee.Initialize()
            image = ee.Image(asset_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display 
            band_res_list = []
            for iband in band_list :
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + '--' + str(round(res))+'--m')
                
            parameters[1].filter.list = band_res_list

        # Capture the suggested scale value based on selected bands 
        band_str = parameters[1].valueAsText
        if band_str :
            # Remove ' in band string in case users add it
            if "'" in band_str :
                band_str = band_str.replace("'","")
            bands = band_str.split(';')
            scale_only = [float(iband.split('--')[1]) for iband in bands]
            parameters[2].value = max(scale_only)

        # Disable input feature if map extent is used
        if parameters[4].value : # map extent selected 
            parameters[3].enabled = False
        else :
            parameters[3].enabled = True  

        # Reset band filter list when asset tag is empty 
        if not asset_tag :
            parameters[1].filter.list = []
            
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        asset_tag  = parameters[0].valueAsText
        band_str   = parameters[1].valueAsText
        scale      = parameters[2].valueAsText
        in_poly    = parameters[3].valueAsText
        use_extent = parameters[4].valueAsText
        out_tiff   = parameters[5].valueAsText

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
        if band_str :
            # Remove ' in band string in case users add it
            if "'" in band_str :
                band_str = band_str.replace("'","")
            bands = band_str.split(';')
            bands_only = [iband.split('--')[0] for iband in bands]
            params_dict['bands'] = bands_only

        # Make sure output file name ends with .tif 
        if not out_tiff.endswith('.tif') :
            out_tiff = out_tiff + '.tif'
        
        # Initialize GEE 
        ee.Initialize()
        # Check GEE image projection
        image = ee.Image(asset_tag)
        # CRS could be other projections than 'EPSG:4326' for some GEE assets
        # When multiple band, select one for projection   
        img_prj = image.select(0).projection().crs().getInfo()
        arcpy.AddMessage('Image projection is '+ img_prj)

        # Get the region of interests
        # Use map view extent if checked 
        if use_extent == 'true' :
            # Get the current project
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            # Get the active map view
            map_view = aprx.activeView
            # Get the current camera object, which includes the map view extent
            camera = map_view.camera  
        
            # Extract the projection and the boundary coordinates (extent)
            spatial_ref = camera.getExtent().spatialReference
            xmin = camera.getExtent().XMin
            ymin = camera.getExtent().YMin
            xmax = camera.getExtent().XMax
            ymax = camera.getExtent().YMax   
            # Check if projection code is 4326 
            poly_prj = spatial_ref.PCSCode
            arcpy.AddMessage('Current map view projection is '+ str(poly_prj))
            if str(poly_prj) not in img_prj : 
                arcpy.AddMessage('Projecting the coordinates of map view extent to '+ img_prj + ' ...')
                # Convert the extent corners to EPSG 4326
                xmin_wgs84, ymin_wgs84 = project_to_wgs84(xmin, ymin, spatial_ref)
                xmax_wgs84, ymax_wgs84 = project_to_wgs84(xmax, ymax, spatial_ref)
                roi = ee.Geometry.BBox(xmin_wgs84, ymin_wgs84, xmax_wgs84, ymax_wgs84)
            else :
                # use the map extent directly if it is already 4326
                roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)

        # Use input feature layer as ROI
        else :
            spatial_ref = arcpy.Describe(in_poly).spatialReference
            poly_prj = spatial_ref.PCSCode
            arcpy.AddMessage('Input feature layer projection is '+ str(poly_prj))
            
            # Project input feature to GEE image coordinate system if needed
            target_poly = in_poly
            if str(poly_prj) not in img_prj :
                arcpy.AddMessage('Projecting input feature layer to GEE image cooridnate system ...')
                out_sr = arcpy.SpatialReference(int(img_prj.split(':')[1]))
                arcpy.Project_management(in_poly, "poly_temp", out_sr)
                target_poly = 'poly_temp'

            # convert input feature to geojson
            arcpy.FeaturesToJSON_conversion(target_poly, 'temp.geojson', "FORMATTED", "", "", "GEOJSON")

            # Read the GeoJSON file
            upper_path = os.path.dirname(arcpy.env.workspace)
            file_geojson = os.path.join(upper_path, 'temp.geojson')
            with open(file_geojson) as f:
                geojson_data = json.load(f)

            # Collect polygon object coordinates
            coords = []
            for feature in geojson_data['features'] :
                coords.append(feature['geometry']['coordinates'])
            arcpy.AddMessage('Total number of polygon objects: '+ str(len(coords)))

            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)
            # Delete temporary geojson 
            arcpy.management.Delete(file_geojson)

        # Clip image to ROI only
        image = image.clip(roi)

        params_dict['region'] = roi # The region to clip and download
        if scale :
            params_dict['scale'] = float(scale) # Resolution in meters per pixel
        params_dict['format'] = 'GEO_TIFF' # The file format of the downloaded image

        # Specify the download parameters
        download_url = image.getDownloadURL(params_dict)

        arcpy.AddMessage('Download URL is: ' + download_url)
        arcpy.AddMessage('Downloading to ' + out_tiff + ' ...')

        response = requests.get(download_url)
        with open(out_tiff, 'wb') as fd:
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
            parameterType="Required")
        param0.dialogref = ""

        param1 = arcpy.Parameter(
            name="bands",
            displayName="Specify the Bands for Download",
            datatype="GPString",
            direction="Input",
            multiValue=True, 
            parameterType="Optional")

        param2 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a Polygon or Polyline as Region of Interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional")
        
        param3 = arcpy.Parameter(
            name="use_extent",
            displayName="Use current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional")

        param4 = arcpy.Parameter(
            name="out_tiff",
            displayName="Specify the Output File Name",
            datatype="DEFile",
            direction="Output",
            parameterType="Required")
        
        params = [param0,param1,param2, param3, param4]

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
            # Only initialize ee when asset tag is given 
            ee.Initialize()
            image = ee.Image(asset_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display 
            band_res_list = []
            for iband in band_list :
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + '--' + str(round(res))+'--m')
                
            parameters[1].filter.list = band_res_list

        # Disable input feature if map extent is used
        if parameters[3].value :
            parameters[2].enabled = False
        else :
            parameters[2].enabled = True  

        # Reset band filter list when asset tag is empty 
        if not asset_tag :
            parameters[1].filter.list = []

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

        # Make sure maximum 3 bands selected 
        band_str   = parameters[1].valueAsText
        if band_str:
            if "'" in band_str :
                band_str = band_str.replace("'","")
            bands = band_str.split(';')
            if len(bands) > 3 :
                parameters[1].setErrorMessage("You can only select up to 3 bands.")
            else :
                parameters[1].clearMessage()

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        asset_tag  = parameters[0].valueAsText
        band_str   = parameters[1].valueAsText
        in_poly    = parameters[2].valueAsText
        use_extent = parameters[3].valueAsText
        out_tiff   = parameters[4].valueAsText

        # Define a function to project a point to WGS 84 (EPSG 4326)
        def project_to_wgs84(x, y, in_spatial_ref):
            point = arcpy.Point(x, y)
            point_geom = arcpy.PointGeometry(point, in_spatial_ref)
            wgs84 = arcpy.SpatialReference(4326)
            point_geom_wgs84 = point_geom.projectAs(wgs84)
            return point_geom_wgs84.centroid.X, point_geom_wgs84.centroid.Y
        
        # Convert BBox to Polygon
        def bbox_to_polygon(in_bbox) :
            # Get the coordinates from the BBox
            coords = in_bbox.coordinates().getInfo()
            # Create the ee.Geometry.Polygon
            out_poly = ee.Geometry.Polygon(coords)            
            return out_poly 

        # Initialize parameters for getDownloadURL
        params_dict = {}
        params_dict['fileFormat'] = 'GEO_TIFF'
        params_dict['assetId'] = asset_tag
        
        # Add bands to vis_params if specfied 
        if band_str :
            # Remove ' in band string in case users add it
            if "'" in band_str :
                band_str = band_str.replace("'","")
            bands = band_str.split(';')
            bands_only = [iband.split('--')[0] for iband in bands]
            params_dict['bandIds'] = bands_only

        # Make sure output file name ends with .tif 
        if not out_tiff.endswith('.tif') :
            out_tiff = out_tiff + '.tif'
        
        # Initialize GEE 
        ee.Initialize()
        # Check GEE image projection
        image = ee.Image(asset_tag)
        # CRS could be other projections than 'EPSG:4326' for some GEE assets
        # When multiple band, select one for projection   
        img_prj = image.select(0).projection().crs().getInfo()
        arcpy.AddMessage('Image projection is '+ img_prj)

        # Get the region of interests
        # Use map view extent if checked 
        if use_extent == 'true' :
            # Get the current project
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            # Get the active map view
            map_view = aprx.activeView
            # Get the current camera object, which includes the map view extent
            camera = map_view.camera  
        
            # Extract the projection and the boundary coordinates (extent)
            spatial_ref = camera.getExtent().spatialReference
            xmin = camera.getExtent().XMin
            ymin = camera.getExtent().YMin
            xmax = camera.getExtent().XMax
            ymax = camera.getExtent().YMax   
            # Check if projection code is 4326 
            poly_prj = spatial_ref.PCSCode
            arcpy.AddMessage('Current map view projection is '+ str(poly_prj))

            if str(poly_prj) not in img_prj : 
                arcpy.AddMessage('Projecting the coordinates of map view extent to '+ img_prj + ' ...')
                # Convert the extent corners to EPSG 4326
                xmin_wgs84, ymin_wgs84 = project_to_wgs84(xmin, ymin, spatial_ref)
                xmax_wgs84, ymax_wgs84 = project_to_wgs84(xmax, ymax, spatial_ref)
                bbox = ee.Geometry.BBox(xmin_wgs84, ymin_wgs84, xmax_wgs84, ymax_wgs84)
            else :
                bbox = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
            roi = bbox_to_polygon(bbox)
        # Use input feature layer as ROI
        else :
            spatial_ref = arcpy.Describe(in_poly).spatialReference
            poly_prj = spatial_ref.PCSCode
            arcpy.AddMessage('Input feature layer projection is '+ str(poly_prj))
            
            # Project input feature to GEE image coordinate system if needed
            target_poly = in_poly
            if str(poly_prj) not in img_prj :
                arcpy.AddMessage('Projecting input feature layer to GEE image cooridnate system ...')
                out_sr = arcpy.SpatialReference(int(img_prj.split(':')[1]))
                arcpy.Project_management(in_poly, "poly_temp", out_sr)
                target_poly = 'poly_temp'

            # convert input feature to geojson
            arcpy.FeaturesToJSON_conversion(target_poly, 'temp.geojson', "FORMATTED", "", "", "GEOJSON")

            # Read the GeoJSON file
            upper_path = os.path.dirname(arcpy.env.workspace)
            file_geojson = os.path.join(upper_path, 'temp.geojson')
            with open(file_geojson) as f:
                geojson_data = json.load(f)

            # Collect polygon object coordinates
            coords = []
            for feature in geojson_data['features'] :
                coords.append(feature['geometry']['coordinates'])
            arcpy.AddMessage('Total number of polygon objects: '+ str(len(coords)))

            # Create an Earth Engine MultiPolygon from the GeoJSON
            roi = ee.Geometry.MultiPolygon(coords)
            # Delete temporary geojson 
            arcpy.management.Delete(file_geojson)

        params_dict['region'] = roi.toGeoJSON()

        #arcpy.AddMessage(roi.toGeoJSON())

        # Clip image to ROI only
        #image = image.clip(multi_polygon)

        # Use ee.data.getPixels to get the pixel data
        pixels = ee.data.getPixels(params_dict)

        # Save the pixel data to a file
        with open(out_tiff, 'wb') as f:
            f.write(pixels)

        arcpy.AddMessage('Saving file to path: '+ out_tiff)
        # Add out tiff to map layer
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.activeMap
        aprxMap.addDataFromPath(out_tiff)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

# Download GEE Image in Large Size through XEE + RasterIO
class DownloadLargeImage:
    
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download GEE Image in Large Size"
        self.description = ""
        self.category = ""
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""

        # Image collection inputs are optional
        param0 = arcpy.Parameter(
            name="ic_asset_tag",
            displayName="Specify GEE Image Collection Asset Tag",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")
        param0.dialogref = "Browse all available datasets from GEE website, copy and paste the asset tag here."

        param1 = arcpy.Parameter(
            name="filter_dates",
            displayName="Filter by dates in YYYY-MM-DD",
            datatype="GPValueTable",
            direction="Input", 
            parameterType="Optional")
        param1.columns = [['GPString','Starting Date'],['GPString', 'Ending Date']] 
        param1.value = [['2014-03-01','2014-05-01']]

        param2 = arcpy.Parameter(
            name="filter_bounds",
            displayName="Filter by location in coordinates",
            datatype="GPValueTable",
            direction="Input", 
            parameterType="Optional")
        param2.columns = [['GPString','Longitude'],['GPString', 'Latitude']]

        param3 = arcpy.Parameter(
            name="use_centroid",
            displayName="Use the center of the current map view extent",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional")
        
        param4 = arcpy.Parameter(
            name="img_asset_tag",
            displayName="Specify Image Asset Tag or Select Image ID",
            datatype="GPString",
            direction="Input",
            multiValue=True,
            parameterType="Required")

        param5 = arcpy.Parameter(
            name="bands",
            displayName="Specify the Bands for Download",
            datatype="GPString",
            direction="Input",
            multiValue=True, 
            parameterType="Required")
        
        param6 = arcpy.Parameter(
            name="scale",
            displayName="Specify the Scale for Download",
            datatype="GPDouble",
            direction="Input",
            multiValue=False, 
            parameterType="Required")        

        param7 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a Polygon as Region of Interest",
            datatype="GPFeatureLayer",
            direction="Input",
            parameterType="Optional")
        
        param8 = arcpy.Parameter(
            name="use_extent",
            displayName="Use the Current Map View Extent as Region of Interest",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional")

        param9 = arcpy.Parameter(
            name="out_folder",
            displayName="Specify the Output Folder",
            datatype="DEFolder",
            direction="Input",
            parameterType="Required")
        
        param10 = arcpy.Parameter(
            name="load_tiff",
            displayName="Load Output Files into Map View after Download",
            datatype="GPBoolean",
            direction="Input",
            parameterType="Optional")
        
        params = [param0,param1,param2, param3, param4, param5,
                  param6,param7,param8, param9, param10]
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
        if parameters[1].valueAsText :
            val_list = parameters[1].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
        else :
            start_date = None
            end_date = None
            
        # Get the filter bounds
        if parameters[3].value : # use map extent
            # Disable input coordinates if map extent is used
            parameters[2].enabled = False
            # Get the current project
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
            poly_prj = spatial_ref.PCSCode
            # Always using latitude and longtiude for ee.Geometry, ee will automatically transform
            if str(poly_prj) not in 'EPSG:4326' : 
                # Convert the extent corners to EPSG 4326
                xmin, ymin = project_to_wgs84(xmin, ymin, spatial_ref)
                xmax, ymax = project_to_wgs84(xmax, ymax, spatial_ref)
            # Get the centroid of map extent 
            lon = (xmin+xmax)/2
            lat = (ymin+ymax)/2
        else : # use input lat/lon
            parameters[2].enabled = True  
            if parameters[2].valueAsText :
                val_list = parameters[2].values
                lon = val_list[0][0]
                lat = val_list[0][1]
            else :
                lon = None
                lat = None

        # Check image list of a given collection asset 
        asset_tag = parameters[0].valueAsText

        # Image collection size could be huge, may take long time to load image IDs without filters
        # Only retrieve the list of images, when either filter dates or filter bounds are selected
        if asset_tag and ((start_date and end_date) or (lon and lat)):
            # Only initialize ee when asset tag is given 
            ee.Initialize()
            collection = ee.ImageCollection(asset_tag)
            # Filter image collection as specified
            if lon is not None and lat is not None :
                collection = collection.filterBounds(ee.Geometry.Point((float(lon), float(lat))))
            if start_date is not None and end_date is not None  :
                collection = collection.filterDate(start_date, end_date)
            # Get image IDs from collection
            image_ids = collection.aggregate_array('system:index').getInfo()
            parameters[4].filter.list = image_ids

        # Check the band list of the first selected image, assuming all selected images have the same bands  
        img_ids = parameters[4].valueAsText
        # Update only when filter list is empty 
        if img_ids and not parameters[5].filter.list :
            # Get the first select image 
            img_id = img_ids.split(';')[0]
            # Only initialize ee when image asset tag is given 
            if asset_tag :
                img_tag = asset_tag + '/' + img_id
            else :
                # If asset tag is not given, have to initilize ee here
                ee.Initialize()
                img_tag = img_id 
            image = ee.Image(img_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display 
            band_res_list = []
            for iband in band_list :
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + '--' + str(round(res))+'--m')
            parameters[5].filter.list = band_res_list

        # Reset band filter list when asset tag changes 
        if (not parameters[4].valueAsText) and (not parameters[0].valueAsText)  :
            parameters[5].filter.list = []

        # Capture the suggested scale value based on selected bands 
        band_str = parameters[5].valueAsText
        if band_str :  
            # Remove ' in band string in case users add it
            if "'" in band_str :
                band_str = band_str.replace("'","")
            bands = band_str.split(';')
            scale_only = [float(iband.split('--')[1]) for iband in bands]
            parameters[6].value = max(scale_only)

        # Disable input feature if map extent is used
        if parameters[8].value : # map extent selected 
            parameters[7].enabled = False
        else :
            parameters[7].enabled = True  
            
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Multiple images could be selected 
        asset_tag  = parameters[0].valueAsText
        img_ids    = parameters[4].valueAsText
        band_str   = parameters[5].valueAsText
        scale      = parameters[6].valueAsText
        in_poly    = parameters[7].valueAsText
        use_extent = parameters[8].valueAsText
        out_folder = parameters[9].valueAsText
        load_tiff  = parameters[10].valueAsText

        # Define a function to project a point to WGS 84 (EPSG 4326)
        def project_to_wgs84(x, y, in_spatial_ref):
            point = arcpy.Point(x, y)
            point_geom = arcpy.PointGeometry(point, in_spatial_ref)
            wgs84 = arcpy.SpatialReference(4326)
            point_geom_wgs84 = point_geom.projectAs(wgs84)
            return point_geom_wgs84.centroid.X, point_geom_wgs84.centroid.Y
        
        # Define a function to clip each image
        def clip_image(image, polygon):
            return image.clip(polygon)
        
        # Filter image by bands if specified 
        #if band_str : # now band_str is required
        # Remove ' in band string in case user adds it
        if "'" in band_str :
            band_str = band_str.replace("'","")
        bands = band_str.split(';')
        bands_only = [iband.split('--')[0] for iband in bands]
        arcpy.AddMessage('Bands selected: ' + ','.join(bands_only))

        # Initialize GEE and get asset 
        ee.Initialize()

        icount = 1
        out_tiff_list = []
        # Iterate each selected image 
        for img_id in img_ids.split(';') :
            # For image collection, concatenate to get the image asset tag
            if asset_tag :
                img_tag = asset_tag + '/' + img_id
            else :
                img_tag = img_id 
            # Must be image collection to convert to xarray 
            image = ee.ImageCollection(ee.Image(img_tag))
            # Filter image by selected bands
            image = image.select(bands_only)

            # Only needs to run the ROI and scale once
            if icount == 1 : 
                # Check GEE image projection
                # CRS could be other projections than 'EPSG:4326' for some GEE assets
                # When multiple band, select the first one for projection   
                img_prj = image.first().select(0).projection().crs().getInfo()
                arcpy.AddMessage('Image projection is '+ img_prj)

                # Get the region of interests
                # Use map view extent if checked 
                if use_extent == 'true' :
                    # Get the current project
                    aprx = arcpy.mp.ArcGISProject("CURRENT")
                    # Get the active map view
                    map_view = aprx.activeView
                    # Get the current camera object, which includes the map view extent
                    camera = map_view.camera  
                
                    # Extract the projection and the boundary coordinates (extent)
                    spatial_ref = camera.getExtent().spatialReference
                    xmin = camera.getExtent().XMin
                    ymin = camera.getExtent().YMin
                    xmax = camera.getExtent().XMax
                    ymax = camera.getExtent().YMax   
                    # Check if projection code is EPSG:4326 
                    # GEE uses EPSG:4326 for filtering and clipping by default  
                    poly_prj = spatial_ref.PCSCode # projected
                    if poly_prj == 0 :
                        poly_prj = spatial_ref.GCSCode # geographic
                    arcpy.AddMessage('Current map view projection is '+ str(poly_prj))
                    if str(poly_prj) not in 'EPSG:4326' : 
                        arcpy.AddMessage('Projecting the coordinates of map view extent to EPSG:4326 ...')
                        # Convert the extent corners to EPSG 4326
                        xmin_wgs84, ymin_wgs84 = project_to_wgs84(xmin, ymin, spatial_ref)
                        xmax_wgs84, ymax_wgs84 = project_to_wgs84(xmax, ymax, spatial_ref)
                        roi = ee.Geometry.BBox(xmin_wgs84, ymin_wgs84, xmax_wgs84, ymax_wgs84)
                    else :
                        # use the map extent directly if it is already 4326
                        roi = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
                # Use input feature layer as ROI
                else :
                    spatial_ref = arcpy.Describe(in_poly).spatialReference
                    poly_prj = spatial_ref.PCSCode
                    if poly_prj == 0 :
                        poly_prj = spatial_ref.GCSCode
                    arcpy.AddMessage('Input feature layer projection is '+ str(poly_prj))
                    
                    # Project input feature to GEE image coordinate system if needed
                    target_poly = in_poly
                    if str(poly_prj) not in 'EPSG:4326' :
                        arcpy.AddMessage('Projecting input feature layer to EPSG:4326 ...')
                        out_sr = arcpy.SpatialReference(4326)
                        arcpy.Project_management(in_poly, "poly_temp", out_sr)
                        target_poly = 'poly_temp'

                    # convert input feature to geojson
                    arcpy.FeaturesToJSON_conversion(target_poly, 'temp.geojson', "FORMATTED", "", "", "GEOJSON")

                    # Read the GeoJSON file
                    upper_path = os.path.dirname(arcpy.env.workspace)
                    file_geojson = os.path.join(upper_path, 'temp.geojson')
                    with open(file_geojson) as f:
                        geojson_data = json.load(f)

                    # Collect polygon object coordinates
                    coords = []
                    for feature in geojson_data['features'] :
                        coords.append(feature['geometry']['coordinates'])
                    arcpy.AddMessage('Total number of polygon objects: '+ str(len(coords)))

                    # Create an Earth Engine MultiPolygon from the GeoJSON
                    roi = ee.Geometry.MultiPolygon(coords)
                    # Delete temporary geojson 
                    arcpy.management.Delete(file_geojson)

                # Get the scale for xarray  
                if scale :
                    scale_ds = float(scale)
                else :
                    # get scale from the first selected band
                    scale_ds = image.first().select(0).projection().nominalScale().getInfo()
                    arcpy.AddMessage('Scale of the first selected band is used: '+ str(scale_ds))
                # Use the crs code from the first selected band
                crs = image.first().select(0).projection().getInfo()['crs']

            # Clip the image using input polygon
            #if in_poly :
            #    arcpy.AddMessage('Clip image by the input polygon ...') 
            #    image = image.map(lambda image: clip_image(image, roi))

            # Use Xarray + RasterIO
            # Convert image to xarray dataset
            ds = xarray.open_dataset(image, engine='ee', crs=crs, scale=scale_ds, geometry=roi)
            transform = from_origin(ds['X'].values[0], ds['Y'].values[0], scale_ds, -scale_ds)
            meta = {
                'driver': 'GTiff',
                'height': ds[bands_only[0]].shape[2],
                'width': ds[bands_only[0]].shape[1],
                'count': len(bands_only),  # Number of bands
                'dtype': ds[bands_only[0]].dtype,  # Data type of the array
                'crs': crs,  # Coordinate Reference System, change if needed
                'transform': transform
            }

            # Store band names
            band_names = {}
            i = 1
            for iband in bands_only :
                band_names['band_'+str(i)] = iband
                i += 1 

            # Create output file name based on image tags  
            out_tiff = os.path.join(out_folder, img_tag.replace('/','_')+ '.tif')
            out_tiff_list.append(out_tiff)

            # Write the array to a multiband GeoTIFF file
            arcpy.AddMessage('Save image to '+ out_tiff + ' ...')
            i = 1
            with rasterio.open(out_tiff, 'w', **meta) as dst:
                for iband in bands_only :
                    dst.write(np.transpose(ds[iband].values[0]), i)  # Write the band
                    i += 1
                # write band names into output tiff 
                dst.update_tags(**band_names)

            icount += 1

        # Add out tiff to map layer
        if load_tiff == 'true' :
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            aprxMap = aprx.activeMap
            for out_tiff in out_tiff_list :
                aprxMap.addDataFromPath(out_tiff)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return