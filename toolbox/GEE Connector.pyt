# -*- coding: utf-8 -*-

import arcpy
import ee
import os
import json
import requests
import xarray

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        tools = []
        tools.append(GEEAuth)
        tools.append(AddImage2Map)
        tools.append(AddImgCol2Map)
        tools.append(AddFeatCol2Map)
        tools.append(DownloadSmallImage)
        tools.append(DownloadImagePixels)
        
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
        # Read JSON key file
        #json_key = 'D:/GEE_connector/crafty-apex-361902-d01e7b50d1ba.json'
        json_key = parameters[0].valueAsText
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
                ee.Initialize(project='crafty-apex-361902')
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
                band_res_list.append(iband + '_' + str(round(res))+'m')
                
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
            bands_only = [iband.split('_')[0] for iband in bands]
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
            tsl.name = img_label + '_' + '_'.join(bands_only)
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
            parameterType="Required")
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
            name="use_extent",
            displayName="Use the centroid of the current map view extent",
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
            img_tag = asset_tag + '/' + img_id
            image = ee.Image(img_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            # Add band resolution information to display 
            band_res_list = []
            for iband in band_list :
                band_tmp = image.select(iband)
                proj = band_tmp.projection()
                res = proj.nominalScale().getInfo()
                band_res_list.append(iband + '_' + str(round(res))+'m')
            parameters[5].filter.list = band_res_list
        
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
        img_tag = asset_tag + '/' + img_id 

        # Define visualization parameters
        vis_params = {}

        # Add bands to vis_params if specfied 
        if band_str :
            # Remove ' in band string in case users add it
            if "'" in band_str :
                band_str = band_str.replace("'","")
            bands = band_str.split(';')
            bands_only = [iband.split('_')[0] for iband in bands]
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
            tsl.name = img_tag + '_' + '_'.join(bands_only)
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
            name="color",
            displayName="Specify the color for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")
        
        param2 = arcpy.Parameter(
            name="point_shape",
            displayName="Specify the point shape for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")
        param2.filter.list = ['circle','square','diamond','cross','plus','triangle']
        
        param3 = arcpy.Parameter(
            name="point_size",
            displayName="Specify the point size for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional")
        param3.filter.list = [2,4,6,8,10]
        
        param4 = arcpy.Parameter(
            name="line_width",
            displayName="Specify the line width for visualization ",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional")
        param4.filter.list = [1,2,3,4,5]
        
        param5 = arcpy.Parameter(
            name="line_type",
            displayName="Specify the line type for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")
        param5.filter.list = ['solid','dotted','dashed']
        
        param6 = arcpy.Parameter(
            name="fill_color",
            displayName="Specify the fill color of polygons for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")

        param7 = arcpy.Parameter(
            name="opacity",
            displayName="Specify the opacity for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional")
        # Set the value range
        param7.filter.type = "Range"
        param7.filter.list = [0, 1]
    
        params = [param0,param1,param2,param3,param4,param5,param6,param7]
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
        """
        The source code of the tool.
        """
        asset_tag  = parameters[0].valueAsText
        feat_color = parameters[1].valueAsText
        point_shape= parameters[2].valueAsText
        point_size = parameters[3].valueAsText
        line_width = parameters[4].valueAsText
        line_type  = parameters[5].valueAsText
        fill_color = parameters[6].valueAsText
        opacity    = parameters[7].valueAsText

        # Define visualization parameters
        vis_params = {}

        # Add color to vis_params if specified 
        if feat_color :
            vis_params['color'] = feat_color
        # Add point shape and size if specified 
        if point_shape :
            vis_params['pointShape'] = point_shape
        if point_size :
            vis_params['pointSize'] = int(point_size)
        # Add line width and type if specified
        if line_width :
            vis_params['width'] = int(line_width)
        if line_type :
            vis_params['lineType'] = line_type 
        
        # Add fill color and opacity if specified 
        if fill_color :
            vis_params['fillColor'] = fill_color
        if opacity :
            vis_params['fillColorOpacity'] = float(opacity) 
        
        # Initialize GEE, initial project is saved in Gcloud application default login JSON
        ee.Initialize()
        # Get image by label  
        collection = ee.FeatureCollection(asset_tag)
        # Get the map ID and token
        map_id_dict = collection.getMapId(vis_params)

        # Construct the URL
        map_url = f"https://earthengine.googleapis.com/v1alpha/{map_id_dict['mapid']}/tiles/{{z}}/{{x}}/{{y}}"

        # Add map URL to the current ArcMap 
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.listMaps("Map")[0]
        tsl = aprxMap.addDataFromPath(map_url)
        tsl.name = asset_tag 
                
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
    
# Download GEE Image in Small Chunk Max. 48MB
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
                band_res_list.append(iband + '_' + str(round(res))+'m')
                
            parameters[1].filter.list = band_res_list

        # Disable input feature if map extent is used
        if parameters[3].value :
            parameters[2].enabled = False
        else :
            parameters[2].enabled = True  
            
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
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

        # Initialize parameters for getDownloadURL
        params_dict = {}
        
        # Add bands to vis_params if specfied 
        if band_str :
            # Remove ' in band string in case users add it
            if "'" in band_str :
                band_str = band_str.replace("'","")
            bands = band_str.split(';')
            bands_only = [iband.split('_')[0] for iband in bands]
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
        #params_dict['scale'] = 30 # Resolution in meters per pixel (30m for Landsat)
        params_dict['format'] = 'GEO_TIFF' # The file format of the downloaded image

        # Specify the download parameters
        download_url = image.getDownloadURL(params_dict)

        arcpy.AddMessage('Download URL is: ' + download_url)
        arcpy.AddMessage('Downloading to ' + out_tiff + ' ...')

        response = requests.get(download_url)
        with open(out_tiff, 'wb') as fd:
            fd.write(response.content)

        # # Download image from URL to zipped tiff
        # out_zip = out_tiff.replace('.tif','.zip')
        # response = requests.get(download_url)
        # with open(out_zip, 'wb') as fd:
        # fd.write(response.content)
        
        # # Unzip file to tiff
        # with zipfile.ZipFile(out_zip) as z:
        #     z.extractall(os.path.dirname(out_tiff))
        # os.remove(out_zip)        

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

# Download by Getting Image Pixels Max. 3 Bands and 48MB     
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
                band_res_list.append(iband + '_' + str(round(res))+'m')
                
            parameters[1].filter.list = band_res_list

        # Disable input feature if map extent is used
        if parameters[3].value :
            parameters[2].enabled = False
        else :
            parameters[2].enabled = True  

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
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
            bands_only = [iband.split('_')[0] for iband in bands]
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

        arcpy.AddMessage(roi.toGeoJSON())

        # Clip image to ROI only
        #image = image.clip(multi_polygon)

        # Use ee.data.getPixels to get the pixel data
        pixels = ee.data.getPixels(params_dict)

        # Save the pixel data to a file
        with open(out_tiff, 'wb') as f:
            f.write(pixels)



        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

# Download GEE Image in Large Size through XEE
class DownloadLargeImage:
    
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download GEE Image in Large Size"
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
                band_res_list.append(iband + '_' + str(round(res))+'m')
                
            parameters[1].filter.list = band_res_list

        # Disable input feature if map extent is used
        if parameters[3].value :
            parameters[2].enabled = False
        else :
            parameters[2].enabled = True  
            
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
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

        # Initialize parameters for getDownloadURL
        params_dict = {}
        
        # Add bands to vis_params if specfied 
        if band_str :
            # Remove ' in band string in case users add it
            if "'" in band_str :
                band_str = band_str.replace("'","")
            bands = band_str.split(';')
            bands_only = [iband.split('_')[0] for iband in bands]
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
        #params_dict['scale'] = 30 # Resolution in meters per pixel (30m for Landsat)
        params_dict['format'] = 'GEO_TIFF' # The file format of the downloaded image

        # Specify the download parameters
        download_url = image.getDownloadURL(params_dict)

        arcpy.AddMessage('Download URL is: ' + download_url)
        arcpy.AddMessage('Downloading to ' + out_tiff + ' ...')

        response = requests.get(download_url)
        with open(out_tiff, 'wb') as fd:
            fd.write(response.content)

        # # Download image from URL to zipped tiff
        # out_zip = out_tiff.replace('.tif','.zip')
        # response = requests.get(download_url)
        # with open(out_zip, 'wb') as fd:
        # fd.write(response.content)
        
        # # Unzip file to tiff
        # with zipfile.ZipFile(out_zip) as z:
        #     z.extractall(os.path.dirname(out_tiff))
        # os.remove(out_zip)        

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return