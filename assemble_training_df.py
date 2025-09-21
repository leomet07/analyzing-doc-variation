import numpy as np
import pandas as pd
import os
import rasterio
import rasterio.features
import sys
from tqdm import tqdm
from shapely.geometry import Point

import adk_data

if len(sys.argv) < 2:
    print("Please specify the out directory.")
    exit(1)

tif_dir = sys.argv[1]
tif_paths = list(os.listdir(tif_dir))


def get_bands_from_tif(tif_path):
    with rasterio.open(tif_path) as src:
        profile = src.profile  # Get the profile of the existing raster
        transform = src.transform
        tags = src.tags()
        scale = tags["scale"]
        x_res = src.res[0]  # same as src.res[1]
        closest_insitu_date = tags["closest_insitu_date"]
        permanent_id = tags["permanent_id"]

        bands = src.read()

        # replace all -infs with nan
        bands[~np.isfinite(bands)] = np.nan

        bands[bands > 0.1] = (
            np.nan
        )  # keep array shape but remove high reflectance outliers (clouds)
        # also this removes acolite outofbound nan values (10^36)

        return (
            bands,
            profile,
            transform,
            scale,
            x_res,
            closest_insitu_date,
            permanent_id,
        )


training_entries = []

for filename in tqdm(tif_paths[3:]):
    tif_filepath = os.path.join(tif_dir, filename)
    current_training_entry = {}
    try:
        (
            bands,
            profile,
            transform,
            scale,
            x_res,
            closest_insitu_date,
            permanent_id,
        ) = get_bands_from_tif(tif_filepath)
    except rasterio.errors.RasterioIOError:
        continue

    # matched doc
    all_doc = adk_data.adk_df[
        (adk_data.adk_df["Permanent_"] == permanent_id)
        & (adk_data.adk_df["sampledate"] == closest_insitu_date)
    ]["doc"]

    try:
        doc = all_doc.item()
    except ValueError:  # array either has 2+ or 0 items
        if len(all_doc) > 0:  # means 2+ measurements for that date, take mean
            doc = all_doc.mean()
        else:
            print("No DOC values found for that date.")

    if not np.isfinite(doc):
        continue

    current_training_entry["doc"] = doc

    # get lat and long
    centroid_point = adk_data.points_shp[
        adk_data.points_shp["Permanent_"] == permanent_id
    ][
        "geometry"
    ].item()  # take first entry of geometry

    centroid_lat = centroid_point.y
    centroid_long = centroid_point.x

    radius_in_meters = 60
    circle = Point(centroid_long, centroid_lat).buffer(
        x_res * (radius_in_meters / float(scale))
    )  # however many x_res sized pixels needed for buffer of radius at downloaded scale

    outside_circle_mask = rasterio.features.geometry_mask(
        [circle], bands[0].shape, transform
    )

    for band in bands:
        band[outside_circle_mask] = (
            np.nan
        )  # arrays store pointer to ratio array, this is okay bc just a mutation

    not_enough_pixels = False
    for band in bands:
        valid_pixels = band[np.isfinite(band)]
        if len(valid_pixels) < 3:
            not_enough_pixels = True

    if not_enough_pixels:
        continue

    # now, can take means safely
    band_names = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"]
    for band_index in range(
        len(band_names)
    ):  # in case tif has extra bands we don't care about
        band = bands[band_index]
        band_name = band_names[band_index]
        mean_value = np.nanmean(band)
        current_training_entry[band_name] = mean_value

    # Recod alg name
    current_training_entry["lake_permanent_id"] = permanent_id

    training_entries.append(current_training_entry)

training_df = pd.DataFrame(training_entries)
print("Training data: \n", training_df)

training_df.to_csv(f"{os.path.basename(tif_dir)}_training_data.csv", index=False)
