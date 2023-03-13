import time
import os
import glob

import fiona
from matplotlib import pyplot as plt
import numpy as np
from shapely import geometry

# if your Planet API Key is not set as an environment variable, you can paste it below
if os.environ.get('PL_API_KEY', ''):
    API_KEY = os.environ.get('PL_API_KEY', '')
else:
    pass

shape_path = '/home/greenberg/Documents/PHD/Projects/high_mountain_asia/high_mountain_asia.gpkg'
polygon_name = shape_path.split('/')[-1].split('.')[0]
with fiona.open(shape_path, layer=polygon_name) as layer:
    for feature in layer:
        print(feature)
        geom = feature['geometry']
        poly = geometry.Polygon(geom['coordinates'][0])

# get images that overlap with our AOI 
geometry_filter = {
  "type": "GeometryFilter",
  "field_name": "geometry",
  "config": geom 
}

years = [
#     [2009, 2010],
#     [2010, 2011],
#     [2011, 2012],
#     [2012, 2013],
#     [2013, 2014],
#     [2014, 2015],
#     [2015, 2016],
#     [2016, 2017],
#     [2017, 2018],
    [2018, 2019],
    [2019, 2020],
]
for [syear, eyear] in years:
    print(syear)
    # get images acquired within a date range
    date_range_filter = {
      "type": "DateRangeFilter",
      "field_name": "acquired",
      "config": {
        "gte": f"{syear}-01-01T00:00:00.000Z",
        "lte": f"{eyear}-01-01T00:00:00.000Z"
      }
    }

    cloud_thresh = 0.2
    # only get images which have <50% cloud coverage
    cloud_cover_filter = {
      "type": "RangeFilter",
      "field_name": "cloud_cover",
      "config": {
        "lte": cloud_thresh
      }
    }
    usable_thresh = 0.8
    usable_data_filter = {
      "type": "RangeFilter",
      "field_name": "usable_data",
      "config": {
        "gte": usable_thresh 
      }
    }

    # combine our geo, date, cloud filters
    combined_filter = {
      "type": "AndFilter",
      "config": [
        geometry_filter, 
        date_range_filter, 
        cloud_cover_filter, 
        usable_data_filter
      ]
    }

    import copy
    import json
    import requests
    from requests.auth import HTTPBasicAuth
    import geopandas as gpd

    # item_type = "REScene"
    item_type = "REOrthoTile"

    # API request object
    search_request = {
      "item_types": [item_type], 
      "filter": combined_filter,
    }

    # fire off the POST request
    search_result = requests.post(
        'https://api.planet.com/data/v1/quick-search',
        auth=HTTPBasicAuth(API_KEY, ''),
        json=search_request
    )

    geojson = search_result.json()
    current = copy.deepcopy(geojson)
    links = [current['_links']['_self']]
    data = {
        'id': [],
        'cloud_cover': [],
        'usable_data': [],
        'black_fill': [],
    }
    geometry = []
    while current['_links'].get('_next'):
        search_result = requests.get(
            current['_links'].get('_next'),
            auth=HTTPBasicAuth(API_KEY, ''),
        )
        current = search_result.json()
        links.append(current['_links']['_self'])
        print(current['_links'].get('_next'))
        images = list(current.items())[1][1]
        for image in images:
            data['id'].append(image['id'])
            data['cloud_cover'].append(image['properties']['cloud_cover'])
            data['usable_data'].append(image['properties']['usable_data'])
            data['black_fill'].append(image['properties']['black_fill'])
            geometry.append(image['geometry'])


    import pandas
    import geopandas as gpd
    from shapely.geometry import Polygon

    df = pandas.DataFrame(data=data)
    df['year'] = syear
    polys = []
    for shape in geometry:
        polys.append(Polygon(shape['coordinates'][0]))
    df = gpd.GeoDataFrame(df, geometry=polys)
    df.to_file(f'hme_swaths_{syear}.gpkg', layer=f'hme_swaths_{syear}', driver="GPKG")




# let's look at the first result
images = list(geojson.items())[1][1]
print(len(images))
# extract image IDs only
image_ids = [feature['id'] for feature in geojson['features']]
print(image_ids)
image_ids = image_ids[-3:]



item_type = "REScene"
# item_type = "REOrthoTile"
download_request = {
    "name": 'download_test',
    "source_type": "scenes",
    "products": [
    {
        "item_ids": image_ids,
        "item_type": item_type,
        "product_bundle": "analytic_sr"
    }],
    "tools": [
        {"clip": {"aoi": geom}},
        {"composite": {}}
    ]
}

download_result = requests.post(
    'https://api.planet.com/compute/ops/orders/v2',
    auth=HTTPBasicAuth(API_KEY, ''),
    json=download_request
)
r = download_result.json()
print(r)

# Returns JSON metadata for assets in this ID. Learn more: planet.com/docs/reference/data-api/items-assets/#asset
result = requests.get(
    id0_url,
    auth=HTTPBasicAuth(API_KEY, '')
)

# List of asset types available for this particular satellite image
print(result.json().keys())

asset_type = 'analytic_sr'
print(result.json()[asset_type]['status'])

# Parse out useful links
links = result.json()[asset_type]["_links"]
self_link = links["_self"]
activation_link = links["activate"]

# Request activation
activate_result = requests.get(
    activation_link,
    auth=HTTPBasicAuth(API_KEY, '')
)

activation_result = 'inactive'
while activation_result != 'active':
    activation_status_result = requests.get(
        self_link,
        auth=HTTPBasicAuth(API_KEY, '')
    )

    activation_result = activation_status_result.json()["status"]
    print(activation_result)
    time.sleep(60)

# Download
download_link = activation_status_result.json()["location"]
result = requests.get(
    download_link,
    auth=HTTPBasicAuth(API_KEY, '')
)
open('test.tif', 'wb').write(result.content)

thumbnail_link = links['thumbnail']
result = requests.get(
    thumbnail_link,
    auth=HTTPBasicAuth(API_KEY, '')
)
open('thumb.jpb', 'wb').write(result.content)



