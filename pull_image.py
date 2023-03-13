import time
import os
import glob

import fiona
from matplotlib import pyplot as plt
import numpy as np
from shapely import geometry
import copy
import json
import requests
from requests.auth import HTTPBasicAuth


if os.environ.get('PL_API_KEY', ''):
    API_KEY = os.environ.get('PL_API_KEY', '')
else:
    pass


image_ids = ['20100825_051647_4756005_RapidEye-2']
item_type = "REOrthoTile"
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
}

download_result = requests.post(
    'https://api.planet.com/compute/ops/orders/v2',
    auth=HTTPBasicAuth(API_KEY, ''),
    json=download_request
)
r = download_result.json()
print(r)

asset_type = 'analytic_sr'
links = r["_links"]
while True:
    download_result = requests.get(
        links['_self'],
        auth=HTTPBasicAuth(API_KEY, '')
    )
    r = download_result.json()
    print(r['state'])
    time.sleep(60)

results = r['_links']['results']

for result in results:
    name = result['name'].split('/')[-1]
    location = result['location']
    result = requests.get(
        location,
        auth=HTTPBasicAuth(API_KEY, '')
    )
    open(name, 'wb').write(result.content)
