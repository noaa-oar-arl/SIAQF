import glob
import numpy as np
import pandas as pd
import xarray as xr

def viirs_loader(filename, varname):
    ds = xr.open_dataset(filename, decode_times=False)
    data = np.squeeze(ds[varname].data)
    data[data < 0] = np.nan
    return data

def tempo_loader(filename, varname):
    if (varname == "latitude") or (varname == "longitude"):
        ds = xr.open_dataset(filename)
    else:
        ds = xr.open_dataset(filename, group="product")
    data = np.squeeze(ds[varname].data)
    data[data < 0] = np.nan
    return data

def aqs_txt_loader(file_path, timestamp, varname, rollback_length):
    simulation_time = pd.to_datetime(timestamp, format="%Y%m%d%H")
    lookback_time = pd.date_range(end=(simulation_time - pd.Timedelta("1 hour")), periods=rollback_length, freq="h")
    lookback_date = lookback_time.strftime("%Y%m%d")

    lon = []
    lat = []
    data = []
    for date in np.unique(lookback_date):
        filename = glob.glob(f"{file_path}/siteeva_12km_{varname}_{date[:6]}.txt")[0]
        df = pd.read_csv(filename, delimiter=",")
        df = df.loc[df[" DD"] == int(date[6:])]

        hour = lookback_time[lookback_date == date].strftime("%H").astype("int")
        for hh in hour:
            lon += [df.loc[df[" HH"] == hh, " LON"].values]
            lat += [df.loc[df[" HH"] == hh, " LAT"].values]
            data += [df.loc[df[" HH"] == hh, " OBS"].values]
    return lon, lat, data

def airnow_dat_loader(file_path, timestamp, varname, rollback_length):
    ds = xr.open_dataset("./fix/airnow2aqm_grid_idx.nc")
    station_id = ds["station_id"].data
    ds.close()

    simulation_time = pd.to_datetime(timestamp, format="%Y%m%d%H")
    lookback_time = pd.date_range(end=(simulation_time - pd.Timedelta("1 hour")), periods=rollback_length, freq="h")
    lookback_time = lookback_time.strftime("%Y%m%d%H")

    data = []
    for time in lookback_time:
        filename = glob.glob(f"{file_path}/HourlyAQObs_{time}.dat")[0]
        if len(filename) == 0:
            df = np.empty(len(station_id))
            df[:] = np.nan
        else:
            df = pd.read_csv(filename, usecols=["AQSID", "Latitude", "Longitude", varname])
            df = df.set_index("AQSID").reindex(station_id)
        data += [np.array(df)]
        del [filename, df]
    data = np.stack(data, 0)
    return data
