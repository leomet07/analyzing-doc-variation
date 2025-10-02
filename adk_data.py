import pandas as pd
import numpy as np
import geopandas
import os
import matplotlib.pyplot as plt

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

# Merge in data from shape file
adk_df = pd.merge(adk_df, bounds_shp, on="Permanent_")

adk_df.to_csv("debug_adk_df_out.csv")

# unique lakes
unique_lakes_ids = np.unique(adk_df["Permanent_"])


def plot_column_vs_column(
    df: pd.DataFrame,
    title_prefix: str,
    xname: str,
    yname: str,
    xunit=None,
    yunit=None,
    plot_line_of_best_fit=False,
    ax=None,
):
    if not ax:
        fig, ax = plt.subplots()

    df = df.dropna(axis=0, subset=([xname, yname]))

    xs = df[xname]
    ys = df[yname]

    ax.scatter(xs, ys)

    if plot_line_of_best_fit:
        plot_line_of_best_fit_for_date_x(xs, ys, ax)

    ax.set_xlabel(f"{xname}" + (f"[{xunit}]" if xunit else ""))
    ax.set_ylabel(f"{yname}" + (f"[{yunit}]" if yunit else ""))
    ax.set_title(f"{title_prefix}: {xname} vs {yname}")
    return xs, ys, ax


# helper function to plot line of best fit
def plot_line_of_best_fit_for_date_x(xs: pd.Series, ys: pd.Series, ax):
    if len(xs) == 0 or len(ys) == 0:
        print("Can't fit line when there is no xs.")
        return
    xs_seconds = xs.values.astype(np.int64) // 10**9

    m, b = np.polyfit(xs_seconds, ys, 1)
    print(f"y = {m}x + {b}")

    ys_pred = xs_seconds * m + b
    ax.plot(xs, ys_pred, color="red")


if __name__ == "__main__":
    print("Number of unique lakes: ", len(unique_lakes_ids))

    plot_column_vs_column(
        adk_df, "All data plot of", "sampledate", "doc", plot_line_of_best_fit=True
    )

    plot_column_vs_column(
        adk_df, "All data plot of", "sampledate", "chla", plot_line_of_best_fit=True
    )
    plot_column_vs_column(
        adk_df, "All data plot of", "sampledate", "secchi", plot_line_of_best_fit=True
    )
    plot_column_vs_column(
        adk_df, "All data plot of", "sampledate", "colort", plot_line_of_best_fit=True
    )

    plot_column_vs_column(
        adk_df,
        "All data plot of",
        "area_ha",
        "doc",
        "hA",
    )
    plt.xlim(0, 500)

    print("Most frequent lake names: ")
    most_frequent_lake_permanent_ids = (
        adk_df.dropna(axis=0, subset=(["doc", "chla"]))["Permanent_"]
        .value_counts()
        .nlargest(4)
        .index.to_list()
    )
    docfig, docaxs = plt.subplots(2, 2)
    chlafig, chlaaxs = plt.subplots(2, 2)
    for index in range(len(most_frequent_lake_permanent_ids)):
        pmid = most_frequent_lake_permanent_ids[index]
        this_lake_df = adk_df[adk_df["Permanent_"] == pmid]
        lake_name = this_lake_df["GNIS_Name"].iloc[0]
        print(f"{lake_name} | Permanent ID: {pmid}")

        plot_column_vs_column(
            this_lake_df,
            f"{lake_name} plot of",
            "sampledate",
            "doc",
            plot_line_of_best_fit=True,
            ax=docaxs.flatten()[index],
        )
        plot_column_vs_column(
            this_lake_df,
            f"{lake_name} plot of",
            "sampledate",
            "chla",
            plot_line_of_best_fit=True,
            ax=chlaaxs.flatten()[index],
        )
    docfig.tight_layout()
    chlafig.tight_layout()

    plt.tight_layout()
    plt.show()
