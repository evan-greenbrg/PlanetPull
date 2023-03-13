import os
import timeit
import math

from matplotlib import pyplot as plt
import pandas
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn import tree, metrics
import rasterio
import geopandas as gpd
from rasterio import plot
from rasterio.mask import mask


def generateTreeShape(raster, water, land):
    # Load in the raster
    ds = rasterio.open(raster)
    bandnames = ['Blue', 'Green', 'Red', 'Red Edge', 'NIR']
    image = ds.read()

    # Generate water points
    water = gpd.read_file(water)
    out, _ = mask(ds, water.geometry, invert=False, filled=False)
    mask_ar = np.invert(out.mask)
    data = out.data

    band_data = {name: [] for name in bandnames}
    for i, name in enumerate(band_data.keys()):
        band_data[name] = data[i][mask_ar[i]]

    water_df = pandas.DataFrame(band_data)
    water_df['class'] = [1 for i in range(len(water_df))]

    # Generate land points
    land = gpd.read_file(land)
    out, _ = mask(ds, land.geometry, invert=False, filled=False)
    mask_ar = np.invert(out.mask)
    data = out.data

    band_data = {name: [] for name in bandnames}
    for i, name in enumerate(band_data.keys()):
        band_data[name] = data[i][mask_ar[i]]

    not_water_df = pandas.DataFrame(band_data)
    not_water_df['class'] = [0 for i in range(len(not_water_df))]

    # Set up whole df
    df = pandas.concat([water_df, not_water_df])

    # Remove Nan
    df = df.dropna(how='any')

    # Initialize tree
    clf = DecisionTreeClassifier(
        random_state=0, 
        max_depth=5
    )

    feature_cols = [b for b in bandnames]
    x_train, x_test, y_train, y_test = train_test_split(
        df[feature_cols], 
        df['class'], 
        test_size=0.1, 
        random_state=1
    )

    clf = clf.fit(
        x_train,
        y_train
    )

    y_pred = clf.predict(x_test)
    print("Accuracy:", metrics.accuracy_score(y_test, y_pred))

    return clf


def predictPixels(inpath, opath, clf):

    ds = rasterio.open(inpath)
    bandnames = ['Blue', 'Green', 'Red', 'Red Edge', 'NIR']
    image = ds.read()

    # Reshape to correct shape
    new_shape = (image.shape[1] * image.shape[2], image.shape[0])
    image_predict = np.moveaxis(image, 0, -1)
    img_as_array = image_predict[:, :, :].reshape(new_shape)
    print('Reshaped from {o} to {n}'.format(
        o=image.shape,
        n=img_as_array.shape)
    )

    # Crazy method to predict for each pixel
    predictions = np.empty([img_as_array.shape[0],])
    predictions[:] = None
    for i, row in enumerate(img_as_array):
        if len(row[~np.isnan(row)]) > 0:
            predictions[i] = clf.predict(row.reshape(1, len(bandnames)))[0]

    # Reshape our classification map
    class_prediction = predictions.reshape(image_predict[:, :, 0].shape)
    print(class_prediction.shape)
#    class_prediction = class_prediction[0, :, :]

    # Reshape our classification map
#    class_prediction = class_prediction.reshape(img[:, :, 0].shape)

    # Output Class Predictions
    meta = ds.meta.copy()
    meta.update({'dtype': rasterio.int8, 'count': 1})
    with rasterio.open(opath, "w", **meta) as dest:
        dest.write(class_prediction.astype(rasterio.int8), 1)

    return class_prediction 



raster = '/home/greenberg/Code/Github/PlanetPull/4756005_2010-08-25_RE2_3A_Analytic_SR.tif'
out = '/home/greenberg/Code/Github/PlanetPull/4756005_2010-08-25_RE2_3A_Analytic_SR_WATER.tif'
water = '/home/greenberg/Documents/PHD/Projects/high_mountain_asia/water_epsg.gpkg'
land = '/home/greenberg/Documents/PHD/Projects/high_mountain_asia/land_epsg.gpkg'

clf = generateTreeShape(raster, water, land)
pred = predictPixels(raster, out, clf)

