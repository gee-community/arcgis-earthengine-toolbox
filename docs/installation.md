## Conda Environement Setup For Earth Engine API  

### Step 1 - Open ArcGIS Python Command Prompt 

Go to **Start Menu** -> **All Apps** -> **ArcGIS folder** -> **Python Command Prompt**, click to run 


### Step 2 - Set up the Conda Environment

By default, conda will always install the newest version of the selected package. However, it is not always the case for ArcGIS users. For example, `ArcPro 3.4` has `python=3.11.10` installed, while `ArcPro 3.3` has `python=3.11.8` installed. Therefore, it is necessary to check the pacakge version first before installation.  

1. List all available conda environements using the following command. The default ArcPro package should be `arcgispro-py3`. 

    `conda env list`

2. List the versions of `python` and `arcpy` installed in `arcgispro-py3` package. The user needs to install the same versions in the new conda environement. For example, `ArcPro 3.3` should have the `python=3.11.8` and `arcpy=3.3`.

    `conda list python`

    `conda list arcpy`

3. Create a new conda environment named `gee` using the listed python version from esri channel. For example, if the listed version is `python=3.11.8`, replace the `LISTED_PYTHON_VERSION` with `3.11.8`. 

    `conda create esri::python=LISTED_PYTHON_VERSION -n gee`


4. (**Optional**) Initialize conda for the proper shell. It is suggested to run this command for the first time of using `conda activate`. After runing the following command, please make sure to restart the Python Command Prompt. 

    `conda init cmd.exe` 

5. Activate the new conda environement `gee`. 

    `conda activate gee` 

6. (**Optional**) Disable the SSL verification. It is suggested to run this command for the first time of using `conda install`.

    `conda config --set ssl_verify false`

7. Install `arcpy` with the listed version from esri channel. For example, if the listed version is `arcpy=3.3`, replace the `LISTED_ARCPY_VERSION` with `3.3`.   

    `conda install arcpy=LISTED_ARCPY_VERSION -c esri`

8. Install `earthengine-api`, `xarray`, and `xee` from conda forge channel. It is recommended to use `conda install` instead of `mamba install`, because `mamba install` may not work properly with `earthengine-api` and `xee`. 

    `conda install earthengine-api xarray xee -c conda-forge`

9. Install specific versions of `gdal` and `rasterio`. The current default version of `gdal=3.9.2` and `rasterio=1.3.10` are incompatible.

    `conda install gdal=3.8.1 rasterio=1.3.9 -c conda-forge`
    
10. Activate package `gee` within ArcPro

    `proswap gee` 
    

After running the above commands, close Python Command Prompt, and start ArcPro. The default environment is now `gee`. The `earthengine-api` is ready for authentication. 

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