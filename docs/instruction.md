# User Instruction

## Authentication Tools

### GEE Authentication

#### Parameters
 1. Google Cloud project ID

This script authenticates access to Google Earth Engine using a Google Cloud Project ID. To use Earth Engine you'll need access to a Cloud project that:
1.	has the Earth Engine API enabled,
2.	is registered for commercial or noncommercial use, and
3.	grants you (or the user) the correct roles and permissions.
For more information, please visit this [link](https://developers.google.com/earth-engine/guides/access). 

Please note that if you have installed Google Cloud SDK shell and set up the application default credentials, this script will authenticate using the quota project ID in the `application_default_credentials.json` located at `C:\Users\user_name\AppData\Roaming\gcloud`. If you don't have Google Cloud SDK shell, the script will authenticate through web browser.   

### Change Project ID 

#### Parameters
 1. Current project ID (automatically displays)
 2. New project ID

This script displays the current Google Cloud quota project ID and allows users to switch quota project ID associated with Google Earth Engine.

Please note that if you have installed Google Cloud SDK shell, you cannot switch quota project ID with this script. Instead, open the Google Cloud SDK shell, copy and paste command `gcloud auth application-default set-quota-project QUOTA_PROJECT_ID`, replace the `QUOTA_PROJECT_ID` with your target project ID.  


## Data Exploration Tools 

### Add GEE Feature Collection to Map by Asset Tag
### Add GEE Feature Collection to Map by Serialized Object 
### Add GEE Image to Map by Asset Tag
### Add GEE Image to Map by Serialized Object
### Add GEE Image Collection to Map by Asset Tag
### Add GEE Image Collection to Map by Serialized Object

## Data Management Tools

### Convert Google Cloud Storage File to GEE Asset
### Download GEE Image Collection to GIF
### Download GEE Image in Large Size
### Save GEE Asset to Serialized JSON File
### Upload Files to Goolge Cloud Storage and Convert to GEE Asset

## Data Processing Tools

### Apply Filters to GEE Datasets
### Apply Map Functions to GEE Datasets
### Apply Reducers to GEE Datasets
### EE Operation
### Run User-Provided Python Script