
import numpy as np
import xarray as xr
from aqm_loaders import aqm_loader
from obs_loaders import airnow_dat_loader

class airnow2aqm_regridder():
    def __init__(self):
        self.varlist = ["OZONE", "PM25"]
        #["NO2", "NH3", "HCHO", "OZONE", "PM25"]

    def read_aqm_coords(self, OUTPUT_PATH):
        lon = aqm_loader("./fix/grid_spec.nc", "grid_lont")
        lat = aqm_loader("./fix/grid_spec.nc", "grid_latt")
        return lon, lat

    def read_grid_idx(self):
        ds = xr.open_dataset("./fix/airnow2aqm_grid_idx.nc")
        return ds["station_ix"].data, ds["station_iy"].data 

    def regridder(self, INPUT_PATH, OUTPUT_PATH, REGRID_FILE, TIMESTAMP, ROLLBACK=24):
        aqm_grid_lon, aqm_grid_lat = self.read_aqm_coords(OUTPUT_PATH)
        station_ix, station_iy = self.read_grid_idx()

        rollback_hour = np.arange(-1*ROLLBACK, 0)
        grid_yt = np.arange(aqm_grid_lat.shape[0]) + 1
        grid_xt = np.arange(aqm_grid_lat.shape[1]) + 1

        # regridded aqs dataset
        ds_gridded = xr.Dataset(
            coords={
                "time": ("time", rollback_hour),
                "yt": ("grid_yt", grid_yt),
                "xt": ("grid_xt", grid_xt),
                "grid_lat": (("yt", "xt"), aqm_grid_lat),
                "grid_lon": (("yt", "xt"), aqm_grid_lon)
            }
        )

        for varname in self.varlist:
            airnow_data = airnow_dat_loader(INPUT_PATH, TIMESTAMP, varname, ROLLBACK)

            gridded_data = np.empty([ROLLBACK, len(grid_yt), len(grid_xt)])
            gridded_data[:] = np.nan
            for i in range(ROLLBACK):
                gridded_data[i, station_iy, station_ix] = airnow_data[i, :, -1]
    
            #print(np.nanmin(gridded_data), np.nanmax(gridded_data))
            ds_gridded[varname] = xr.DataArray(gridded_data, dims=["time", "yt", "xt"], coords=[rollback_hour, grid_yt, grid_xt]).fillna(-999)
            del [airnow_data, gridded_data]

        ds_gridded.to_netcdf(REGRID_FILE)
        print(f"Regridded airnow file saved to {REGRID_FILE}")

