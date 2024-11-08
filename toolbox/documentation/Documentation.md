# ArcGEE Connector
An ArcPro Python toolbox for connection to Google Earth Engine (GEE)

## Introduction 
ArcGEE is a Python toolbox for ArcGIS that seamlessly connects the Google Earth Engine API with ArcPro. This integration empowers users to explore, download, analyze, and visualize an extensive repository of Google Earth Engine datasets directly within ArcPro, while also enabling the upload of local datasets to Google Earth Engine assets. By leveraging Google Earth Engine’s scalable computing power and advanced machine learning models, ArcGEE provides a powerful, no-code solution for big data analytics, combining the strengths of both platforms for an enhanced, efficient workflow.

## Conda Environement Setup For Earth Engine API  

### Step 1 - Open ArcGIS Python Command Prompt 

Go to **Start Menu** -> **All Apps** -> **ArcGIS folder** -> **Python Command Prompt**, click to run 


### Step 2 - Create a conda environment

Create a new conda environment, initialize conda for the proper shell if needed, activate the environment, disable SSL verification, install `arcpy` and `earthengine-api`, activate package within ArcPro, install additional package `xee` and `rasterio`, by using the following commands. 

    conda create conda-forge::mamba esri::python -n gee
    conda init cmd.exe 
    conda activate gee 
    conda config --set ssl_verify false
    mamba install arcpy earthengine-api -c esri -c conda-forge 
    proswap gee 
    conda install xee rasterio -c conda-forge

After running the above commands, close Python Command Prompt, and start ArcPro. The default environment is now "gee". The `earthengine-api` is ready for authentication. 

## Download ArcGEE Connector Toolbox

The user can download the ArcGEE Connector Toolbox at this link `https://github.com/di-private/redlands-desktop-engine/tree/woolpert_dev/toolbox`. Download the entire toolbox folder and move it to the ArcPro connected direcotry, the toolbox will automatially appear in the Catalog. 


## Google Cloud SDK

If Google Cloud SDK is installed, the Google Cloud default credentials may affect Google Earth Engine authentication through ArcPro Python script. Therefore, it is recommended to modify Google Cloud default credentials to be consistent with the target Google project for Earth Engine. To achieve this, follow the steps below.

1. In Windows OS, search for "Google Cloud SDK Shell", click to open.
2. Check the active Google account using `gcloud auth list`. Make sure the account aligns with the target Google project for Earth Engine.
3. If the user wants to choose another account, type `gcloud auth login`. The browser will pop up asking user to choose the target Google account for Earth Engine. 
4. Check the active Google project using `gcloud config list`. Make sure the project ID algins with the target Google project for Earth Engine. 
5. If the user wants to choose another project, type `gcloud config set project YOUR_PROJECT_ID`. 
6. Re-authenticate to update the `application_default_credentials.json` file by using `gcloud auth application-default login` or `gcloud auth application-default set-quota-project QUOTA_PROJECT_ID`. Next when user runs "ee.Initialize()", it will automatically refer to the default project in this "application_default_credentials.json" file. 

## Service Account Keys

For the first time of Earth Engine authentication, it is OK to proceed without a JSON key file. However, if the user wants to switch to another project and re-authenticate, the browser cookies and cache or the system environment variables may have stored the previous tokens and always lead to the previous project for authentication. To avoid the re-authentication failure, it is recommended to use a JSON key file of the target Google Cloud project for Earth Engine authentication. To achieve this, follow the steps below. 

Log in to the Google Cloud Console and select the target project.
Go to "IAM & Admin" - > "Service Accounts" - >  select the target "Email" - > choose tab "KEYS" - > Click "ADD KEY" drop-down menu, then select "Create new key" - > Select JSON as the Key type and click Create, then the JSON file will be automatically downloaded to local system and saved to the "Download" folder. 
Move the JSON file to the desired folder for storage and future use.  

## Key Features

 - Add EE to Map 
 - Add GEE Feature Collection to Map 
 - Add GEE Image or Image Collection to Map
 - Apply Filters to GEE Datasets
 - Apply Map Functions to GEE Datasets
 - Download GEE Image Collection to GIF
 - Download GEE Image in Large Size
 - EE Load Asset
 - EE Operation
 - GEE Authentication
 - Upload Files to Goolge Cloud Storage
 
