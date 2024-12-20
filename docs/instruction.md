# User Instruction

## Authentication Tools

### Authenticate Earth Engine

This script authenticates the use of Google Earth Engine with provided Google account. **The user only needs to run this script once on the same computer.** 

The project ID and workload tag are optional inputs here. If the user inputs the project ID, the script will also initialize the Earth Engine.  The user can define them in the "Initialize Earth Engine" script later. To use Earth Engine, you'll need access to a Cloud project that:

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

### Add Feature Collection to Map by Asset Tag

This script adds the Earth Engine Feature Collection dataset to ArcPro as a base map by its asset tag and customizes the visualization parameters. Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited directly. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).

#### Parameters 
 1. Asset tag
 2. Filter by dataset properties
 3. Filter by dates
 4. Filter by point gemoetry in lat/lon coordinates
 5. Filter by the centroid of the current map view
 6. Filter by the extent of the current map view 
 7. Color for visualization
 8. Save the filtered dataset to serialized JSON file


### Add Feature Collection to Map by Serialized Object 

This script adds the Earth Engine Feature Collection dataset to ArcPro as a base map by its serialized JSON object and customizes the visualization parameters. The serialized JSON object is the string representation of the dataset. The user can save the serialized Earth Engine object (Image, Image Collection, Feature, Feature Collection, List, Geometry, etc. ) to JSON file. This is helpful when the user filters the dataset and saves the modified dataset for future access. 

Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).

#### Parameters
1. Serialized JSON file
2. Asset tag of the selected object (automatically displays)
3. Color for visualization

### Add Image to Map by Asset Tag

This script adds the Earth Engine Image dataset to ArcPro as a base map by its asset tag and customizes the visualization parameters. Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).

#### Parameters 

 1. Asset tag
 2. Select bands for visualization (up to 3)
 3. Minimum value for visualization (value to map to 0, up to 3 comma-seperated numbers)
 4. Maximum value for visualization (value to map to 255, up to 3 comma-seperated numbers)
 5. Gamma correction factors (value to multiply each pixel value, up to 3 comma-seperated numbers)
 6. Color palette in CSS-style (single-band images only, comma-separated list of hex strings)
 8. Save the filtered dataset to serialized JSON file

### Add Image to Map by Serialized Object

This script adds the Earth Engine Image dataset to ArcPro as a base map by its serialized JSON object and customizes the visualization parameters. Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).

The user can save the serialized Earth Engine object (Image, Image Collection, Feature, Feature Collection, List, Geometry, etc.) to JSON file, which is the string representation of the dataset. This is helpful when the user filters the dataset and saves the modified dataset for future access. 

#### Parameters 

 1. Serialized JSON file 
 2. Asset tag of the selected object (automatically displays)
 3. Select bands for visualization (up to 3)
 4. Minimum value for visualization (value to map to 0, up to 3 comma-seperated numbers)
 5. Maximum value for visualization (value to map to 255, up to 3 comma-seperated numbers)
 6. Gamma correction factors (value to multiply each pixel value, up to 3 comma-seperated numbers)
 7. Color palette in CSS-style (single-band images only, comma-separated list of hex strings)

### Add Image Collection to Map by Asset Tag

This script adds the Earth Engine Image Collection dataset to ArcPro as a base map by its asset tag and customizes the visualization parameters. **The user can only add one image to ArcPro per run.** Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited directly. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).

#### Parameters 

 1. Asset tag
 2. Filter by dates
 3. Filter by point gemoetry in lat/lon coordinates
 4. Filter by the centroid of the current map view
 5. Select image from the filtered list
 6. Select bands for visualization (up to 3)
 7. Minimum value for visualization (value to map to 0, up to 3 comma-seperated numbers)
 8. Maximum value for visualization (value to map to 255, up to 3 comma-seperated numbers)
 9. Gamma correction factors (value to multiply each pixel value, up to 3 comma-seperated numbers)
 10. Color palette in CSS-style (single-band images only, comma-separated list of hex strings)
 11. Save the filtered dataset to serialized JSON file

### Add Image Collection to Map by Serialized Object

This script adds the Earth Engine Image Collection dataset to ArcPro as a base map by its serialized JSON object and customizes the visualization parameters. **The user can only add one image to ArcPro per run.** Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).

The user can save the serialized Earth Engine object (Image, Image Collection, Feature, Feature Collection, List, Geometry, etc.) to JSON file, which is the string representation of the dataset. This is helpful when the user filters the dataset and saves the modified dataset for future access. 


#### Parameters 
 1. Serialized JSON file
 2. Asset tag of the selected object (automatically displays)
 3. Select image from the filtered list
 4. Select bands for visualization (up to 3)
 5. Minimum value for visualization (value to map to 0, up to 3 comma-seperated numbers)
 6. Maximum value for visualization (value to map to 255, up to 3 comma-seperated numbers)
 7. Gamma correction factors (value to multiply each pixel value, up to 3 comma-seperated numbers)
 8. Color palette in CSS-style (single-band images only, comma-separated list of hex strings)


## Data Management Tools

### Convert Cloud Storage File to Earth Engine Asset

This script converts file(s) in Google Cloud Storage to Earth Engine asset. It is used to share dataset on the Earth Engine platform. The file(s) will be assigned with a user-specified asset tag. 

There are two options to locate the target files: 

1.	If you know the gsutil URI of the target file, just specify the project ID and paste the URI to the file input. If you are dealing with a large bucket with lots of folders and files, it is recommended to use file URI directly. Otherwise, it will take time to locate the file. 
2.	If not, specify the project ID and select the bucket, folder and target file one by one.

You can convert the file(s) to the following types of Earth Engine assets:

1.	Image, when you select one file in `.tif` format
2.	Image collection, when you select multiple files in `.tif` format
3.	Feature collection, when you select one file in `.shp`, `.csv`, `.zip` or `.tfrecord` format. **Each `.zip` file must contain only one shape file with its accessory files.**  
4.	Feature collections, when you select multiple files in `.shp`, `.csv`, `.zip` or `.tfrecord` format. Each file will be converted to a feature collection, respectively. 

#### Parameters 

1. Google Cloud project ID 
2. Select the bucket (skip if you know the file gsutil URI)
3. Select the folder in the bucket (skip if you know the file gsutil URI)
4. Select file(s) in the folder or specify gsutil URI
5. Choose asset type (`image` or `table`)
6. Specify the asset tag/ID

### Download Image by Asset Tag

This script downloads the Earth Engine image dataset to GeoTIFF by its asset tag. It converts Earth Engine image object to xarray dataset using `xee` and writes to local GeoTIFF file using `rasterio`. Theoretically, there is no file size limitation compared to other functions such as `ee.Image.getDownloadURL()` and `ee.data.getPixels()`. Larger files will take longer to download.    

#### Parameters

1. Asset tag
2. Select bands to download
3. Specify the scale in meters (image resolution)
4. Use a polygon feature as region of interest
5. Use the extent of the current map view as region of interest
6. Specify the output GeoTIFF name
7. Check the box to load image to map after download


### Download Image by Serialized Object

This script downloads the Earth Engine image dataset to GeoTIFF by its serialized JSON object. It converts Earth Engine image object to xarray dataset using `xee` and writes to local GeoTIFF file using `rasterio`. Theoretically, there is no file size limitation compared to other functions such as `ee.Image.getDownloadURL()` and `ee.data.getPixels()`. Larger files will take longer to download. 

#### Parameters

1. Serialized JSON file
2. Asset tag of the selected object (automatically displays)
2. Select bands to download
3. Specify the scale in meters (image resolution)
4. Use a polygon feature as region of interest
5. Use the extent of the current map view as region of interest
6. Specify the output GeoTIFF name
7. Check the box to load image to map after download


### Download Image Collection by Asset Tag

This script downloads the Earth Engine image collection dataset to GeoTIFF by its asset tag. It converts Earth Engine image collection object to xarray dataset using `xee` and writes to local GeoTIFF file using `rasterio`. Theoretically, there is no file size limitation compared to other functions such as `ee.Image.getDownloadURL()` and `ee.data.getPixels()`. Larger files will take longer to download. 

#### Parameters

 1. Asset tag
 2. Filter by dates
 3. Filter by point gemoetry in lat/lon coordinates
 4. Filter by the centroid of the current map view
 5. Select images to download
 6. Select bands to download
 7. Specify the scale in meters (image resolution)
 8. Use a polygon feature as region of interest
 9. Use the extent of the current map view as region of interest
 10. Specify the output GeoTIFF name
 11. Check the box to load images to map after download 

### Download Image Collection by Serialized Object

This script downloads the Earth Engine image collection dataset to GeoTIFF by its serialized JSON object. It converts Earth Engine image collection object to xarray dataset using `xee` and writes to local GeoTIFF file using `rasterio`. Theoretically, there is no file size limitation compared to other functions such as `ee.Image.getDownloadURL()` and `ee.data.getPixels()`. Larger files will take longer to download. 

#### Parameters

 1. Serialized JSON file 
 2. Asset tag of the selected object (automatically displays)
 3. Select images to download
 4. Select bands to download
 5. Specify the scale in meters (image resolution)
 6. Use a polygon feature as region of interest
 7. Use the extent of the current map view as region of interest
 8. Specify the output GeoTIFF name
 9. Check the box to load images to map after download 

### Download Image Collection to GIF

### Save Earth Engine Asset to Serialized JSON File

This script exports Earth Engine dataset from an asset tag to a serialized JSON file, allowing for quick access in the future without needing to recall the asset tag.


#### Parameters
 1. Asset tag
 2. Asset type (`Feature Collection`, `Image` or `Image Collection`)
 3. Specify output JSON file name

This script saves Google Earth Engine dataset object from asset tag to serialized JSON file. 

### Upload File to Cloud Storage and Convert to Earth Engine Asset

This script uploads file(s) from local storage to Google Cloud Storage and converts file(s) to Earth Engine asset. It is used to share dataset on Google Cloud and the Earth Engine platform. The file(s) will be assigned with a user-specified asset tag. 

There are two options to locate the target files: 

1.	If you know the gsutil URI of the target file, just specify the project ID and paste the URI to the file input. If you are dealing with a large bucket with lots of folders and files, it is recommended to use file URI directly. Otherwise, it will take time to locate the file. 
2.	If not, specify the project ID and select the bucket, folder and target file one by one.

You can convert the file(s) to the following types of Earth Engine assets:

1.	Image, when you select one file in `.tif` format
2.	Image collection, when you select multiple files in `.tif` format
3.	Feature collection, when you select one file in `.shp`, `.csv`, `.zip` or `.tfrecord` format. **Each `.zip` file must contain only one shape file with its accessory files.**  
4.	Feature collections, when you select multiple files in `.shp`, `.csv`, `.zip` or `.tfrecord` format. Each file will be converted to a feature collection, respectively. 

#### Parameters

1. Google Cloud project ID 
2. Select the bucket
3. Select the folder in the bucket
4. Select file(s) from local storage
5. Check the box to upload to Earth Engine (Optional)
6. Choose asset type (`image` or `table`)
7. Specify the asset tag/ID

## Data Processing Tools

### Apply Filters to GEE Datasets
### Apply Map Functions to GEE Datasets
### Apply Reducers to GEE Datasets
### EE Operation
### Run User-Provided Python Script