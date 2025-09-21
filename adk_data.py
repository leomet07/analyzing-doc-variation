import pandas as pd
import numpy as np
import geopandas
import os

adk_df = pd.read_csv("lagoes_adk_modified.csv")

adk_df["sampledate"] = pd.to_datetime(adk_df["sampledate"], format=f"%m/%d/%y")
# adk_df = adk_df[adk_df["sampledate"].dt.year <= 1986]

adk_df["Permanent_"] = adk_df["Permanent_"].astype(str)

# Load lake bounds shape file
bounds_shp = geopandas.read_file(
    os.path.join(
        "adk-lakes-shapefiles",
        "bounds",
        "adk-lakes-gt.25km2-200m-bound-clean.qmd.shp",
    )
)


# Load centroid shape file
points_shp = geopandas.read_file(
    os.path.join(
        "adk-lakes-shapefiles",
        "points",
        "adk-lakes-gt.25km2-200m-points-clean-296.geojson",
    )
)

# Filter data df to only contain lakes that are in shapefile dataset
adk_df = adk_df[adk_df["Permanent_"].isin(bounds_shp["Permanent_"])]
adk_df = adk_df[adk_df["Permanent_"].isin(points_shp["Permanent_"])]

# unique lakes
unique_lakes_ids = np.unique(adk_df["Permanent_"])

if __name__ == "__main__":
    print("Number of unique lakes: ", len(unique_lakes_ids))
    print()
    print("Ten most frequent lakes:\n", adk_df["Permanent_"].value_counts().nlargest(5))
