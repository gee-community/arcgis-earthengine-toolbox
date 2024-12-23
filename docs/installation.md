# Installation

## Conda Environement Setup For Earth Engine API  

Before starting the installation, ensure that you have the necessary account permissions to create a conda environment and install the required packages. **If your ArcPro was installed by an administrator, you will need administrator-level permissions to complete the installation.**  

For ArcPro version `3.x`, follow the steps below to set up the conda environment. If you have ArcPro version lower than `3.0`, it is suggested that you upgrade it to `3.x`. You can login to your ESRI account, and download the specific ArcPro version from the **Downloads** -> **All Products and Versions** -> **All Versions**.  

### Step 1 - Run ArcGIS Python Command Prompt 

To do this in your Windows computer, go to **Start Menu** -> **All Apps** -> **ArcGIS folder** -> **Python Command Prompt**, click to run. 


### Step 2 - Set up the Conda Environment

Once you run the Python Command Prompt,

1. List all available conda environements using the following command. The default ArcPro package should be `arcgispro-py3`. 

        conda env list

2. You cannot modify the default package `arcgispro-py3`. Instead, clone it to create a new conda environment `gee`. 

        conda create --name gee --clone arcgispro-py3

3. (**Optional**) Initialize conda for the proper shell. It is required to run this command for the first time of using `conda activate`.    

        conda init cmd.exe 

    **After runing the command, please make sure to restart the Python Command Prompt.** To do this, close the current Python Command Prompt window and open a new one.  

4. Activate the new conda environement `gee`. 

        conda activate gee 

5. (**Optional**) Disable the SSL verification. It is suggested to run this command for the first time of using `conda install`.

        conda config --set ssl_verify false

6. Install `earthengine-api` and `xee` from `conda-forge` channel. Please note that these two packages are unavailable in `esri` channel. It is recommended to use `conda install` instead of `mamba install`, because `mamba install` may not work properly with `earthengine-api` and `xee`. 

        conda install earthengine-api xee -c conda-forge

7. Install specific version of `rasterio` from `esri` channel. The default installation version of `rasterio=1.3.10` may be incompatible with ArcPro pre-installed `gdal`.

        conda install rasterio=1.3.9 -c esri
    
8. Activate package `gee` within ArcPro

        proswap gee 
    

After running the above commands, close Python Command Prompt, and start ArcPro. The default conda environment becomes `gee`. To check if the packages have been successufully installed, click **Analysis** -> **Python** -> **Python Window**. Run the following commands. 

    import ee
    import xee
    import rasterio

The `earthengine-api` is then ready for authentication and initialization. 

## Download ArcGEE Connector Toolbox

The user can download the ArcGEE Connector Toolbox at this [link](https://github.com/di-private/redlands-desktop-engine/tree/woolpert_dev/toolbox). Download the entire toolbox folder and move it to the ArcPro connected direcotry, the toolbox will automatially appear in the Catalog. 


## Google Cloud SDK

If Google Cloud SDK is installed, the Google Cloud default credentials may affect Google Earth Engine authentication through ArcPro Python script. Therefore, it is recommended to modify Google Cloud default credentials to be consistent with the target Google project for Earth Engine. To achieve this, follow the steps below.

1. In Windows OS, search for "Google Cloud SDK Shell", click to open.
2. Check the active Google account using `gcloud auth list`. Make sure the account aligns with the target Google project for Earth Engine.
3. If the user wants to choose another account, type `gcloud auth login`. The browser will pop up asking user to choose the target Google account for Earth Engine. 
4. Check the active Google project using `gcloud config list`. Make sure the project ID algins with the target Google project for Earth Engine. 
5. If the user wants to choose another project, type `gcloud config set project YOUR_PROJECT_ID`. 
6. Re-authenticate to update the `application_default_credentials.json` file by using `gcloud auth application-default login` or `gcloud auth application-default set-quota-project QUOTA_PROJECT_ID`. Next when user runs "ee.Initialize()", it will automatically refer to the default project in this "application_default_credentials.json" file. 
