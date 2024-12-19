# User Instruction

## Authentication Tools

### Authenticate Earth Engine

This script authenticates the use of Google Earth Engine with provided Google account. The project ID and workload tag are optional inputs here. If the user inputs the project ID, the script will also initialize the Earth Engine.  The user can define them in the "Initialize Earth Engine" script later. To use Earth Engine, you'll need access to a Cloud project that:

1.	has the Earth Engine API enabled,
2.	is registered for commercial or noncommercial use, and
3.	grants you (or the user) the correct roles and permissions.
For more information, please visit this [link](https://developers.google.com/earth-engine/guides/access). 

Please note that if you have installed Google Cloud SDK shell and set up the application default credentials, this script will authenticate Earth Engine using the quota project ID in the `application_default_credentials.json` usually located at `C:\Users\user_name\AppData\Roaming\gcloud`. If you don't have Google Cloud SDK shell, the script will authenticate through the web browser. 

#### Parameters
 1. Google Cloud project ID (Optional)
 2. Wrokload tag (Optional)


### Check or Change Project ID 

This script displays the current Google Cloud quota project ID and allows users to switch quota project ID and workload tag associated with Google Earth Engine.

Please note that if you have installed Google Cloud SDK shell, you cannot switch quota project ID using this script. Instead, open the Google Cloud SDK shell, copy and paste the following command `gcloud auth application-default set-quota-project QUOTA_PROJECT_ID`, replace the `QUOTA_PROJECT_ID` with your target project ID.

#### Parameters
 1. Current project ID (automatically displays)
 2. Current workload tag (automatically displays)
 3. New project ID (Optional)
 4. New workload tag (Optional)  

  
### Initialize Earth Engine 
The script initialize the use of Google Earth Engine with a project ID and workload tag. The user must assign a project ID to use Earth Engine. **The user will need to run this script every time they start the ArcPro.**  

Workload tags are labels for monitoring specific computations within Earth Engine. The user can monitor and track tagged computations in the Metrics Explorer using the Earth Engine Cloud Project > Project > Used EECUs metric, and grouping or filtering by workload_tag. 
Workload tag must be 1 - 63 characters, beginning and ending with an alphanumeric character ([a-z0-9A-Z]) with dashes (-), underscores (_), dots (.), and alpha numerics between, or an empty string to reset the default back to none.

#### Parameters 
 1. Google Cloud project ID 
 2. Workload tag (Optional)

## Data Exploration Tools 

### Add GEE Feature Collection to Map by Asset Tag

This script adds the Google Earth Engine Feature Collection to ArcPro as a base map by its asset tag and customizes the visualization parameters. Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited directly. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).

#### Parameters 
 1. Asset tag
 2. Filter by feature collection properties
 3. Filter by dates
 4. Filter by point gemoetry in lat/lon coordinates
 5. Filter by the centroid of the current map view
 6. Filter by the extent of the current map view 
 7. Feature collection color for visualization
 8. Save the filtered feature collection to serialized JSON file


### Add GEE Feature Collection to Map by Serialized Object 

This script adds the Google Earth Engine Feature Collection to ArcPro as a base map by its serialized JSON object. Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit https://developers.google.com/earth-engine/datasets/catalog.

The user can save the serialized Google Earth Engine object (Image, Image Collection, Feature, Feature Collection, List, Geometry, etc. ) to JSON file. This is very helpful when the user filters the dataset and saves the modified dataset for future use. 

#### Parameters




### Add GEE Image to Map by Asset Tag
### Add GEE Image to Map by Serialized Object
### Add GEE Image Collection to Map by Asset Tag

#### Parameters 
 1. Asset tag
 2. Bands (up to 3)
 3. Minimum value for visualization
 4. Maximum value for visualization
 5. Gamma correction factors
 6. Color palette in CSS-style

This script adds the Google Earth Engine Image to ArcPro as a base map by its asset tag and customizes the visualization parameters. Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).


### Add GEE Image Collection to Map by Serialized Object

#### Parameters 
 1. Serialized JSON file
 2. Bands (up to 3)
 3. Minimum value for visualization
 4. Maximum value for visualization
 5. Gamma correction factors
 6. Color palette in CSS-style

This script adds the Google Earth Engine Image to ArcPro as a base map by its serialized JSON file and customizes the visualization parameters. 

The user can save the serialized Google Earth Engine object (Image, Image Collection, Feature, Feature Collection, List, Geometry, etc. ) to the JSON file. This is very helpful when the user filters the dataset and saves the modified dataset for future use. 

Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).


## Data Management Tools

### Convert Google Cloud Storage File to GEE Asset
### Download GEE Image Collection to GIF
### Download GEE Image in Large Size
### Save GEE Asset to Serialized JSON File
#### Parameters
 1. Asset tag
 2. Asset type (Feature Collection, Image or Image Collection)
 3. Output JSON file name

This script saves Google Earth Engine dataset object from asset tag to serialized JSON file. 

### Upload Files to Goolge Cloud Storage and Convert to GEE Asset

## Data Processing Tools

### Apply Filters to GEE Datasets
### Apply Map Functions to GEE Datasets
### Apply Reducers to GEE Datasets
### EE Operation
### Run User-Provided Python Script