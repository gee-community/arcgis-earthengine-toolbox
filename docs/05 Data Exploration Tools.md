# ArcGIS Earth Engine Toolbox User Guide: Data Exploration Tools
These tools allow you to visualize Google Earth Engine feature collections, images and images collections from the [Earth Engine data catalog](https://developers.google.com/earth-engine/datasets), or Earth Engine assets within your Google Cloud Project. If you are looking to download data or run analytics, please see the Data Management and Data Processing toolboxes. 
  
## Data Exploration Tools 

### Add Feature Collection to Map by Asset ID

This script adds the Earth Engine Feature Collection dataset to ArcPro as a base map by its asset ID and customizes the visualization parameters. **To avoid slow response, the feature collection size is limited to 100,000 elements.**

Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited directly. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).

![Alt Text](images/AddFC2MapbyID.png)

#### Parameters 
 1. Asset ID
 2. Filter by dataset properties
 3. Filter by dates
 4. Filter by point gemoetry in lat/lon coordinates
 5. Filter by the centroid of the current map view
 6. Filter by the extent of the current map view 
 7. Color for visualization
 8. Save the filtered dataset to serialized JSON file


### Add Feature Collection to Map by Serialized Object 

This script adds the Earth Engine Feature Collection dataset to ArcPro as a base map by its serialized JSON object and customizes the visualization parameters. The serialized JSON object is the string representation of the dataset. The user can save the serialized Earth Engine object (Image, Image Collection, Feature, Feature Collection, List, Geometry, etc. ) to JSON file. This is helpful when the user filters the dataset and saves the modified dataset for future access. 

**To avoid slow response, the feature collection size is limited to 100,000 elements. If the feature collection size is larger than 100,000 elements after filtering, the script will only display the first 100,000 elements.**

![Alt Text](images/AddFC2MapbyJSON.png)

Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).

#### Parameters
1. Serialized JSON file
2. Color for visualization

### Add Image to Map by Asset ID

This script adds the Earth Engine Image dataset to ArcPro as a base map by its asset ID and customizes the visualization parameters. Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).

![Alt Text](images/AddImg2MapbyID.png)

#### Parameters 

 1. Asset ID
 2. Select bands for visualization (up to 3)
 3. Minimum value for visualization (value to map to 0, up to 3 comma-seperated numbers)
 4. Maximum value for visualization (value to map to 255, up to 3 comma-seperated numbers)
 5. Gamma correction factors (value to multiply each pixel value, up to 3 comma-seperated numbers)
 6. Color palette in CSS-style (single-band images only, comma-separated list of hex strings)
 7. Save the filtered dataset to serialized JSON file

### Add Image to Map by Serialized Object

![Alt Text](images/AddImg2MapbyJSON.png)

This script adds the Earth Engine Image dataset to ArcPro as a base map by its serialized JSON object and customizes the visualization parameters. Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).

The user can save the serialized Earth Engine object (Image, Image Collection, Feature, Feature Collection, List, Geometry, etc.) to JSON file, which is the string representation of the dataset. This is helpful when the user filters the dataset and saves the modified dataset for future access. 

#### Parameters 

 1. Serialized JSON file 
 2. Select bands for visualization (up to 3)
 3. Minimum value for visualization (value to map to 0, up to 3 comma-seperated numbers)
 4. Maximum value for visualization (value to map to 255, up to 3 comma-seperated numbers)
 5. Gamma correction factors (value to multiply each pixel value, up to 3 comma-seperated numbers)
 6. Color palette in CSS-style (single-band images only, comma-separated list of hex strings)

### Add Image Collection to Map by Asset ID

This script adds the Earth Engine Image Collection dataset to ArcPro as a base map by its asset tag and customizes the visualization parameters. **The user can only add one image to ArcPro per run.** Please note that the dataset is added as a Tiled Service Layer (TSL), which cannot be edited directly. The user will need to download the dataset for analysis in ArcPro. To browse all datasets, please visit this [link](https://developers.google.com/earth-engine/datasets/catalog).

![Alt Text](images/AddIC2MapbyID.png)

#### Parameters 

 1. Asset ID
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

![Alt Text](images/AddIC2MapbyJSON.png)

The user can save the serialized Earth Engine object (Image, Image Collection, Feature, Feature Collection, List, Geometry, etc.) to JSON file, which is the string representation of the dataset. This is helpful when the user filters the dataset and saves the modified dataset for future access. 


#### Parameters 
 1. Serialized JSON file
 2. Select image from the filtered list
 3. Select bands for visualization (up to 3)
 4. Minimum value for visualization (value to map to 0, up to 3 comma-seperated numbers)
 5. Maximum value for visualization (value to map to 255, up to 3 comma-seperated numbers)
 6. Gamma correction factors (value to multiply each pixel value, up to 3 comma-seperated numbers)
 7. Color palette in CSS-style (single-band images only, comma-separated list of hex strings)
