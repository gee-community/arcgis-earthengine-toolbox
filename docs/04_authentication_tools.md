
# ArcGIS Earth Engine Toolbox (GEE Connector) User Guide: Authentication tools

These tools help you get connected to your cloud project and Earth Engine.

## Authenticate Earth Engine


> [!NOTE]
> If you have already installed Google Cloud SDK, you will need to set up the application default login for Earth Engine authentication. To do this, go to [Installation](03_installation.md) and follow the instructions. This script is for users who do not have Google Cloud SDK.


This script authenticates the use of Google Earth Engine with provided Google account. 
>[!TIP]
>The user only needs to run this script once on the same computer. 

![Alt Text](images/GEEAuth.png)

The project ID and workload tag are optional inputs here. If the user inputs the project ID, the script will also initialize the Earth Engine.  The user can define them in the "Initialize Earth Engine" script later. To use Earth Engine, you'll need access to a Cloud project that:

1.	has the Earth Engine API enabled, refer to [this link](https://developers.google.com/earth-engine/guides/access) for more information.
2.	is registered for commercial or noncommercial use. Earth Engine, Google's geospatial science platform in Google Cloud, is **available for paid commercial use and remains free for academic and research use.** Refer to [this link](https://console.cloud.google.com/earth-engine) to register for commercial use or noncommercial use.
3.	grants you (or the user) the correct roles and permissions.


Please note that if you have installed Google Cloud SDK shell and set up the application default credentials, this script will authenticate Earth Engine using the quota project ID in the `application_default_credentials.json` usually located at `C:\Users\user_name\AppData\Roaming\gcloud`. If you don't have Google Cloud SDK shell, the script will authenticate through the web browser. 

### Parameters
 1. Google Cloud project ID (Optional)
 2. Wrokload tag (Optional)


Here is the video guide for the Earth Engine authentication:

<div align="center">
  <a href="https://www.youtube.com/watch?v=Onke2gSq3wE" target="_blank">
    <img src="https://img.youtube.com/vi/Onke2gSq3wE/0.jpg" alt="Earth Engine Authentication" width="640" height="360" border="10" />
  </a>
</div>


## Check or Change Project ID 

This script displays the current Google Cloud quota project ID and allows users to switch quota project ID and workload tag associated with Google Earth Engine if needed. 

![Alt Text](images/CheckProjectID.png)

Please note that if you have installed Google Cloud SDK shell, you cannot switch quota project ID using this script. Instead, open the Google Cloud SDK shell, copy and paste the following command `gcloud auth application-default set-quota-project QUOTA_PROJECT_ID`, replace the `QUOTA_PROJECT_ID` with your target project ID.

### Parameters
 1. Current project ID (automatically displays)
 2. Current workload tag (automatically displays)
 3. New project ID (Optional)
 4. New workload tag (Optional)  


Here is the video guide for checking or changing project ID and workload tag:

<div align="center">
  <a href="https://www.youtube.com/watch?v=eWkmTi1Vdn4" target="_blank">
    <img src="https://img.youtube.com/vi/eWkmTi1Vdn4/0.jpg" alt="Check or Change Project ID" width="640" height="360" border="10" />
  </a>
</div>

  
## Initialize Earth Engine 
The script initialize the use of Google Earth Engine with a project ID and workload tag. The user must assign a project ID to use Earth Engine. **The user will need to run this script every time they start the ArcPro.**  

![Alt Text](images/GEEInit.png)


### Parameters 
 1. Google Cloud project ID 
 2. Workload tag (Optional)

Here is the video guide for the Earth Engine initialization:

<div align="center">
  <a href="https://www.youtube.com/watch?v=jg1FjUxZ8Tc" target="_blank">
    <img src="https://img.youtube.com/vi/jg1FjUxZ8Tc/0.jpg" alt="Earth Engine Initialization" width="640" height="360" border="10" />
  </a>
</div>

