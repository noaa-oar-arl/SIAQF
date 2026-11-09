
import numpy as np
import xarray as xr
import xesmf as xe
from aqm_loaders import aqm_loader
from obs_loaders import viirs_loader, tempo_loader

class sat2aqm_regridder():
    def __init__(self):
        self.varlist = {
            "viirs": ["AOD550"],
            "tempo": ["vertical_column_troposphere"]
        }
        self.output_varlist = {
            "viirs": ["aod"],
            "tempo": ["no2"]
        }

    def read_aqm_coords(self, OUTPUT_PATH):
        lon = aqm_loader("./fix/grid_spec.nc", "grid_lont")
        lat = aqm_loader("./fix/grid_spec.nc", "grid_latt")
        return lon, lat
    
    def read_sat_coords(self, SAT_PATH, SAT_OPTION):
        if SAT_OPTION == "viirs":
            lon = viirs_loader(SAT_PATH, "lon")
            lat = viirs_loader(SAT_PATH, "lat")
        elif SAT_OPTION == "tempo":
            lon = tempo_loader(SAT_PATH, "longitude")
            lat = tempo_loader(SAT_PATH, "latitude")
        return lon, lat

    def viirs_regridder(self, SAT_FILES, OUTPUT_PATH, REGRID_FILE, TIMESTAMP):
        aqm_grid_lon, aqm_grid_lat = self.read_aqm_coords(OUTPUT_PATH)
        sat_lon, sat_lat = self.read_sat_coords(SAT_FILES[0], "viirs")

        grid_yt = np.arange(aqm_grid_lat.shape[0]) + 1
        grid_xt = np.arange(aqm_grid_lat.shape[1]) + 1

        # viirs-to-aqm regridder
        ds_src = xr.Dataset({
            "lat": (["lat"], sat_lat),
            "lon": (["lon"], sat_lon),
        })
        ds_tgt = xr.Dataset({
            "lat": (["y", "x"], aqm_grid_lat),
            "lon": (["y", "x"], aqm_grid_lon),
        })
        regridder = xe.Regridder(
            ds_src,
            ds_tgt,
            method="bilinear",
            filename="./fix/regrid_viirs_bilinear_1800x3600_544x800.nc",
            reuse_weights=True
        )

        # regridded viirs dataset
        ds_gridded = xr.Dataset(
            coords={
                "time": ("time", [TIMESTAMP]),
                "yt": ("grid_yt", grid_yt),
                "xt": ("grid_xt", grid_xt),
                "grid_lat": (("yt", "xt"), aqm_grid_lat),
                "grid_lon": (("yt", "xt"), aqm_grid_lon)
            }
        )

        for (varname, output_varname) in zip(self.varlist["viirs"], self.output_varlist["viirs"]):
            total_data = []
            for filename in SAT_FILES:
                data_ori = viirs_loader(filename, varname)
                da_src = xr.DataArray(
                    data_ori,
                    dims=("lat", "lon"),
                    coords={"lat": sat_lat, "lon": sat_lon}
                    )
                data_regridded = regridder(da_src).data
                data_regridded[data_regridded < 0] = np.nan
                total_data += [data_regridded]
                del [data_ori, data_regridded, da_src]
            total_data = np.stack(total_data, 0)
            total_data = np.expand_dims(np.nanmean(total_data, axis=0), axis=0)
            ds_gridded[output_varname] = xr.DataArray(total_data, dims=["time", "yt", "xt"], coords=[[TIMESTAMP], grid_yt, grid_xt]).fillna(-999)

        ds_gridded.to_netcdf(REGRID_FILE)
        print(f"Regridded viirs file saved to {REGRID_FILE}")

    def tempo_regridder(self, SAT_FILES, OUTPUT_PATH, REGRID_FILE, TIMESTAMP):
        aqm_grid_lon, aqm_grid_lat = self.read_aqm_coords(OUTPUT_PATH)
        sat_lon, sat_lat = self.read_sat_coords(SAT_FILES[0], "tempo")

        grid_yt = np.arange(aqm_grid_lat.shape[0]) + 1
        grid_xt = np.arange(aqm_grid_lat.shape[1]) + 1

        # tempo-to-aqm regridder
        ds_src = xr.Dataset({
            "lat": (["lat"], sat_lat),
            "lon": (["lon"], sat_lon),
        })
        ds_tgt = xr.Dataset({
            "lat": (["y", "x"], aqm_grid_lat),
            "lon": (["y", "x"], aqm_grid_lon),
        })
        regridder = xe.Regridder(
            ds_src,
            ds_tgt,
            method="bilinear",
            filename="./fix/regrid_tempo_bilinear_2950x7750_544x800.nc",
            reuse_weights=True
        )

        # regridded viirs dataset
        ds_gridded = xr.Dataset(
            coords={
                "time": ("time", [TIMESTAMP]),
                "yt": ("grid_yt", grid_yt),
                "xt": ("grid_xt", grid_xt),
                "grid_lat": (("yt", "xt"), aqm_grid_lat),
                "grid_lon": (("yt", "xt"), aqm_grid_lon)
            }
        )

        for (varname, output_varname) in zip(self.varlist["tempo"], self.output_varlist["tempo"]):
            total_data = []
            for filename in SAT_FILES:
                data_ori = tempo_loader(filename, varname)
                da_src = xr.DataArray(
                    data_ori,
                    dims=("lat", "lon"),
                    coords={"lat": sat_lat, "lon": sat_lon}
                    )
                data_regridded = regridder(da_src).data
                data_regridded[data_regridded <= 0] = np.nan
                total_data += [data_regridded]
                del [data_ori, data_regridded, da_src]
            total_data = np.stack(total_data, 0)
            total_data = np.expand_dims(np.nanmean(total_data, axis=0), axis=0)
            ds_gridded[output_varname] = xr.DataArray(total_data, dims=["time", "yt", "xt"], coords=[[TIMESTAMP], grid_yt, grid_xt]).fillna(-999)

        ds_gridded.to_netcdf(REGRID_FILE)
        print(f"Regridded tempo file saved to {REGRID_FILE}")
