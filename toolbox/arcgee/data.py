# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ee
import ujson
import arcpy
import xee
import google.auth

def auth(project=None):
    credentials, _ = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/earthengine",
        ]
    )
    ee.Initialize(
        credentials.with_quota_project(None),
        project=project,
    )
    
    return


def save_ee_result(ee_object, path):

    serialized_obj = ee_object.serialize()

    with open(path, 'w') as f:
        ujson.dump(serialized_obj, f)

    return

def load_ee_result(path):

    with open(path, 'r') as f:
        ee_object = ujson.load(f)

    return ee.deserializer.fromJSON(ee_object)

def ee_to_tif(ee_img, scale=1000, projection='EPSG:3857', region=None):

    # if region is not defined then request the total image bounds
    if region is None:
        region = ee_img.geometry().bounds()

    ix = xr.open_dataset(
        ee.ImageCollection(ee_img), 
        engine='ee',
        scale=scale,
        projection=projection,
        geometry=region
    )

    return

def _xds_to_rioda(ds):
    return

