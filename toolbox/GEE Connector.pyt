# -*- coding: utf-8 -*-

import arcpy
import ee
import os 

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
            parameters[1].filter.list = band_list
        
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
            vis_params['bands'] = bands

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

        param2 = arcpy.Parameter(
            name="filter_wrs",
            displayName="Filter by WRS Path and Row",
            datatype="GPValueTable",
            direction="Input", 
            parameterType="Optional")
        param2.columns = [['GPString','WRS Path'],['GPString', 'WRS Row']]

        param3 = arcpy.Parameter(
            name="images",
            displayName="Select images by image ID",
            datatype="GPString",
            direction="Input",
            parameterType="Required")
                
        param4 = arcpy.Parameter(
            name="bands",
            displayName="Specify three bands for RGB visualization",
            datatype="GPString",
            direction="Input",
            multiValue=True, 
            parameterType="Optional")
        
        param5 = arcpy.Parameter(
            name="min_val",
            displayName="Specify the minimum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional")

        param6 = arcpy.Parameter(
            name="max_val",
            displayName="Specify the maximum value for visualization",
            datatype="GPDouble",
            direction="Input",
            parameterType="Optional")
        
        param7 = arcpy.Parameter(
            name="gamma",
            displayName="Specify gamma correction factors",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")
        
        param8 = arcpy.Parameter(
            name="palette",
            displayName="Specify color palette in CSS-style color strings for visualization",
            datatype="GPString",
            direction="Input",
            parameterType="Optional")
        
        params = [param0,param1,param2,param3,param4,param5,param6,param7,param8]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # Check image list of a given collection asset 
        asset_tag = parameters[0].valueAsText
        # get the filter dates
        if parameters[1].valueAsText :
            val_list = parameters[1].values
            start_date = val_list[0][0]
            end_date = val_list[0][1]
        else :
            start_date = None
            end_date = None
            
        # Get the filter WRS path and row
        if parameters[2].valueAsText :
            val_list = parameters[2].values
            wrs_path = val_list[0][0]
            wrs_row = val_list[0][1]
        else :
            wrs_path = None
            wrs_row = None
        # image collection size could be huge, may take long to load without filters
        if asset_tag and start_date and end_date:
            # Only initialize ee when asset tag is given 
            ee.Initialize()
            collection = ee.ImageCollection(asset_tag)
            # Filter image collection as specified
            if wrs_path is not None :
                collection = collection.filter(ee.Filter.eq('WRS_PATH', int(wrs_path)))
                
            if wrs_row is not None:
                collection = collection.filter(ee.Filter.eq('WRS_ROW', int(wrs_row)))
                
            if start_date is not None and end_date is not None  :
                collection = collection.filterDate(start_date, end_date)
            # Get image IDs from collection
            image_ids = collection.aggregate_array('system:index').getInfo()
            parameters[3].filter.list = image_ids

        # Check band list of the selected image  
        img_id = parameters[3].valueAsText
        if img_id :
            # Only initialize ee when asset tag is given 
            ee.Initialize()
            img_tag = asset_tag + '/' + img_id
            image = ee.Image(img_tag)
            band_names = image.bandNames()
            band_list = band_names.getInfo()
            parameters[4].filter.list = band_list
        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        asset_tag = parameters[0].valueAsText
        filter_dates = parameters[1].valueAsText
        filter_wrs = parameters[2].valueAsText
        img_id = parameters[3].valueAsText
        band_str = parameters[4].valueAsText
        min_val = parameters[5].valueAsText
        max_val = parameters[6].valueAsText
        gamma_str = parameters[7].valueAsText
        palette_str = parameters[8].valueAsText

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
            vis_params['bands'] = bands

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
        tsl.name = img_tag 
        
        
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
    
# Download GEE Image in Small Chunk Max. 32MB
class DownloadSmallImage:
    
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Image in Small Chunk"
        self.description = ""
        self.category = ""
        self.canRunInBackgroud = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            name="in_poly",
            displayName="Choose a Polygon or Polyline for the Region ",
            datatype="GPFeatureLayer",
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
    
