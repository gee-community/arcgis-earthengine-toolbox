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

import arcpy
import ee

def add_layer(ee_object, vis_params=None, name = None):

    # check if Earth Engine object is a ImageCollection
    # if so, then create a mosaic before
    if isinstance(ee_object, ee.ImageCollection):
        ee_object = ee_object.mosaic()

    map_id_dict = ee_object.getMapId(vis_params)

    aprx = arcpy.mp.ArcGISProject('CURRENT')
    m = aprx.listMaps('Map')[0]
    layer = m.addDataFromPath(map_id_dict['tile_fetcher'].url_format)
    if name is not None:
        layer.name = name

    return