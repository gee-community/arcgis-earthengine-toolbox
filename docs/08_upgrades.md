# ArcGIS Earth Engine Toolbox (GEE Connector) User Guide: Upgrades

## Upgrade ArcGIS Pro

In the future, if you upgrade your ArcGIS Pro to a newer version, for example, from `3.3` to `3.4`, you will need to set up the conda environment again. Because the existing `gee` conda environment is not compatible with the new ArcGIS Pro version. To do this, you need to:

1. Delete the existing conda environment `gee` using the following command:

```bash
    conda env remove --name gee
```

2. Repeat Step 1 and Step 2 of the Conda Environment Setup in the [Installation Guide](03_installation.md) to create the compatible conda environment.

## Upgrade ArcGIS Earth Engine Toolbox

The newest version of the ArcGIS Earth Engine Toolbox will be released on the [ArcGIS Earth Engine Toolbox GitHub repository](https://github.com/gee-community/arcgis-earthengine-toolbox). Please check the repository for the latest version and update your toolbox accordingly.

1. For git users, you can pull the latest version from the repository:

```bash
    git pull
```

2. For non-git users, you can download the latest version from the repository and replace the existing version in your local toolbox folder.
