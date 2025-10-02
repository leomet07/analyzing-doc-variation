import pandas as pd
import numpy as np
import geopandas
import os
import sys
import multiprocessing
from tqdm import tqdm
import fetch_landsat_five_L2
import random
import adk_data

adk_df = adk_data.adk_df.dropna(axis=0, subset=(["doc"]))


# Assemble download params
def gen_all_lakes_all_dates_params(project, OUT_DIR, days_before_and_after_insitu):
    all_params = []
    for index, row in adk_df.iterrows():
        lake_permanent_id = row["Permanent_"]

        sample_date_YYYY_MM_DD = row["sampledate"].strftime(
            f"%Y-%m-%d"
        )  # faster than strftime
        start_date = (
            row["sampledate"] - pd.DateOffset(days=days_before_and_after_insitu)
        ).strftime(f"%Y-%m-%d")
        end_date = (
            row["sampledate"] + pd.DateOffset(days=days_before_and_after_insitu)
        ).strftime(
            f"%Y-%m-%d"
        )  # check for 1, 3, 5 days (this is one day)

        out_filename = f"lake{lake_permanent_id}_{sample_date_YYYY_MM_DD}_index{index}.tif"  # row index guaranteed to not collide

        all_params.append(
            (
                OUT_DIR,
                out_filename,
                project,
                lake_permanent_id,
                start_date,  # YYYY-MM-DD
                end_date,  # YYYY-MM-DD
                sample_date_YYYY_MM_DD,  # insitu date, YYYY-MM-DD
                30,  # scale
                False,  # Should visualize
            )
        )

    return all_params


def wrapper_export(
    args,
):  # this function allows ONE param to be spread onto many params for a function
    fetch_landsat_five_L2.export_raster_main_landsat_five_L2(*args)


if __name__ == "__main__":
    project = sys.argv[1]
    out_dir = sys.argv[2]

    days_before_and_after_insitu = int(sys.argv[3])

    all_params_to_pass_in = gen_all_lakes_all_dates_params(
        project, out_dir, days_before_and_after_insitu
    )

    fetch_landsat_five_L2.open_gee_project(project=project)
    manager = multiprocessing.Manager()
    scale_cache = manager.dict()  # empty by default
    pool = multiprocessing.Pool(25)

    random.shuffle(all_params_to_pass_in)

    # Starmap
    pool.imap(
        wrapper_export,
        tqdm(all_params_to_pass_in, total=len(all_params_to_pass_in)),
    )
    pool.close()
    pool.join()
