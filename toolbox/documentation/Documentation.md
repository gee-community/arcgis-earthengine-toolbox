# ArcGEE Connector
An ArcPro Python toolbox for connection to Google Earth Engine

## Introduction 



## Installation 

### Step 1 - Open ArcGIS Python Command Prompt 

Go to **Start Menu** -> **All Apps** -> **ArcGIS folder** -> **Python Command Prompt**, click to run 


### Step 2 - Create a conda environment

Create a new conda environment, initialize conda for the proper shell if needed, activate the environement, disable SSL verification, install `arcpy` and `earthengine-api`, activate package within ArcPro, install additional package `xee` and `rasterio`, by using the following commands. 

    conda create conda-forge::mamba esri::python -n gee
    conda init cmd.exe 
    conda activate gee 
    conda config --set ssl_verify false
    mamba install arcpy earthengine-api -c esri -c conda-forge 
    proswap gee 
    conda install xee rasterio -c conda-forge




## Key Features

