
import os, sys, glob
import numpy as np
import xarray as xr
import pandas as pd

sys.path.insert(0, "./toolkit")
from aqm_loaders import aqm_loader, aqm_met_loader, aqm_bndy_loader, nexus_emi_loader, plume_emi_loader, fire_emi_loader
from gfs_loaders import gfs_met_loader
from sat2aqm_regridder import sat2aqm_regridder
from airnow2aqm_regridder import airnow2aqm_regridder

class input_generator():
    def namelist_config(self):
        namelist = pd.read_csv("./namelist", header=None, delimiter="=")
        namelist = namelist.rename(columns={0: "key", 1: "value"}).set_index("key")
        namelist = namelist.to_dict()["value"]

        AQM_DATE = namelist["AQM_DATE"]
        AQM_CYCLE = namelist["AQM_CYCLE"]
        MET_OPTION = namelist["MET_OPTION"]
        MET_PATH = namelist["MET_PATH"]
        AQM_PATH = namelist["AQM_PATH"]
        EMI_PATH = namelist["EMI_PATH"]
        VIIRS_PATH = namelist["VIIRS_PATH"]
        TEMPO_PATH = namelist["TEMPO_PATH"]
        OBS_PATH = namelist["OBS_PATH"]
        OUTPUT_PATH = namelist["OUTPUT_PATH"]
        OUTPUT_PATH = f"{OUTPUT_PATH}/{AQM_DATE}/{AQM_CYCLE}"
       
        FCST_LENGTH = int(namelist["FCST_LENGTH"])
        BNDY_LENGTH = int(namelist["BNDY_LENGTH"])
        FCST_LAYER = int(namelist["FCST_LAYER"])  # for AQM, FCST_LAYER=64 for surface
        BNDY_OPTION = namelist["BNDY_OPTION"]  # retro uses AQM dyn files, fcst uses LBC files

        RESTART = namelist["RESTART"] in ["True", "true"]

        FCST_SPECIES = ["NO2", "NH3", "HCHO", "OZONE", "PM25"]
        FCST_OPTION = [
            namelist["NO2"] in ["True", "true"],
            namelist["NH3"] in ["True", "true"],
            namelist["HCHO"] in ["True", "true"],
            namelist["OZONE"] in ["True", "true"],
            namelist["PM25"] in ["True", "true"]
        ]
        FCST_SPECIES = [species for species, opt in zip(FCST_SPECIES, FCST_OPTION) if opt]
        return AQM_DATE, AQM_CYCLE, MET_OPTION, MET_PATH, AQM_PATH, EMI_PATH, VIIRS_PATH, TEMPO_PATH, OBS_PATH, OUTPUT_PATH, FCST_LENGTH, BNDY_LENGTH, FCST_SPECIES, FCST_LAYER, BNDY_OPTION, RESTART
    
    
    def read_static_fields(self, AQM_PATH):
        varlist = ["grid_latt", "grid_lont", "area", "zsurf", "land"]
        offset = [    0,    180,     0,    0,     0]
        scaler = [  100,    100,  1e+8, 1000,     1]
    
        print('Read grid specs from:')
        print("./fix/grid_spec.nc")
        print("./fix/atmos_static.nc")

        total_data = []
        for i in range(len(varlist)):
            if varlist[i] in ["grid_latt", "grid_lont", "area"]:
                data = aqm_loader("./fix/grid_spec.nc", varlist[i])
            elif varlist[i] in ["zsurf", "land"]:
                data = np.squeeze(aqm_loader("./fix/atmos_static.nc", varlist[i]))
            data = (data - offset[i]) / scaler[i]
            total_data += [data]
            del data
        total_data = np.stack(total_data, 0)
        total_data = np.expand_dims(total_data, axis=0)
        print('static', total_data.shape, pd.Timestamp("now"))
        return total_data
    
    
    def read_met_fields(self, MET_OPTION, MET_PATH, AQM_DATE, AQM_CYCLE, FCST_TIME):
        #varlist = ["ugrd10m", "vgrd10m", "hpbl", "spfh2m", "dswrf_ave", "tmp2m", "veg", "tcdc_aveclm", "tprcp", "lhtfl_ave", "fricv", "pressfc", "cnwat", "snowc_ave"]
        #offset = [     0,        0,      0,       0,        0,     200,    0,            0,     0,          0,     0,      5e+4,     0,   0]
        #scaler = [    10,       10,   1e+3,    1e-2,     1e+3,     100,   100,         100,     1,       1e+3,     1,      1e+5,  1e-3,   100]
        
        total_data = []
        if MET_OPTION in ["AQM", "aqm"]:
            for time in FCST_TIME:
                aqm_timestep = pd.to_datetime(time, format="%Y%m%d%H") - pd.Timedelta(hours=int(AQM_CYCLE))
                if aqm_timestep.strftime("%H%M") == "0000":
                    aqm_date = (aqm_timestep - pd.Timedelta(days=1)).strftime("%Y%m%d")
                    aqm_hour = "24"
                else:
                    aqm_date = aqm_timestep.strftime("%Y%m%d")
                    aqm_hour = aqm_timestep.strftime("%H")

                phy_file = f"{AQM_PATH}/{aqm_date}{AQM_CYCLE}/phyf0{aqm_hour}.nc"  
                print(f"Read met from {phy_file}")
                daily_data = aqm_met_loader(phy_file)
                total_data += [daily_data]

        elif MET_OPTION in ["GFS", "gfs"]:
            # use forecast from previous cycle
            aqm_timestep = pd.to_datetime(AQM_DATE, format="%Y%m%d")
            cycle_dict = {
                "00": "18",
                "06": "00",
                "12": "06",
                "18": "12"
            }
            gfs_cycle = cycle_dict[AQM_CYCLE]
            if AQM_CYCLE == "00":
                gfs_date = (aqm_timestep - pd.Timedelta(days=1)).strftime("%Y%m%d")
            else:
                gfs_date = aqm_timestep.strftime("%Y%m%d")

            for hour in range(len(FCST_TIME)):
                gfs_hour = hour + 1 + 6   # account for time differece from previous cycle
                phy_file = f"{MET_PATH}/gfs.{gfs_date}/{gfs_cycle}/atmos/gfs.t{gfs_cycle}z.sfcf0{gfs_hour:02d}.nc"
                print(f"Read met from {phy_file}")
                daily_data = gfs_met_loader(phy_file)
                total_data += [daily_data]

        else:
            print("Met source is not identified. Terminated.")
            sys.exit(1)

        total_data = np.stack(total_data, 0)
        print('met', total_data.shape, pd.Timestamp("now"))
        return total_data


    def read_sat_fields(self, REGRIDDED_SAT_FILES):
        varlist = ["aod", "no2", "o3_avg", "co"]
        offset = [    0,    0,    0,    0]
        scaler = [    1, 1e17,    1,    1]

        total_data = []
        for i in range(2):  #range(len(varlist)):
            ds = xr.open_dataset(REGRIDDED_SAT_FILES[i])
            data = ds[varlist[i]].data
            mask = (data > 0).astype(float)
            data[data == -999] = 0
            data = (data - offset[i]) / scaler[i]
            total_data += [data]
            total_data += [mask]
            ds.close()
            del [ds, data, mask]
        total_data = np.concatenate(total_data, 0)
        #total_data = np.repeat(np.expand_dims(total_data, axis=0), 2, axis=0)
        total_data = np.expand_dims(total_data, axis=0)  # time axis
        print('sat', total_data.shape, pd.Timestamp("now"))
        return total_data
    
    
    def read_lbc_fields(self, EMI_PATH, AQM_CYCLE, FCST_TIME, BNDY_LENGTH, FCST_SPECIES, FCST_LAYER, BNDY_OPTION):
        init_date = (pd.to_datetime(FCST_TIME[0], format="%Y%m%d%H") - pd.Timedelta(hours=int(AQM_CYCLE))).strftime("%Y%m%d")
        init_file = f"{EMI_PATH}/aqm.{init_date}/{AQM_CYCLE}/aqm.t{AQM_CYCLE}z.gfs_data.tile7.halo0.nc"
        species_fulllist = ["NO2", "NH3", "HCHO", "OZONE", "PM25"]
        varlist = ["no2", "nh3", "form", "o3", "pm25_tot"]
        dynlist = ["no2", "nh3", "form", "o3_ave", "pm25_ave"]
        offset = [    0,    0,    0,    0,    0]
        scaler = [ 1e-2, 1e-2, 1e-2, 1e-2,   10]

        total_top = []
        total_bottom = []
        total_left = []
        total_right = []
        for species in FCST_SPECIES:
            try:
                idx = species_fulllist.index(species)
            except Exception as e:
                print(f"LBC loading error: {e}")

            top = [[]]*len(FCST_TIME)
            bottom = [[]]*len(FCST_TIME)
            left = [[]]*len(FCST_TIME)
            right = [[]]*len(FCST_TIME)
            if BNDY_OPTION == "retro":
                # Current retro settings are based on 24h AQMv8 products
                for i in range(len(FCST_TIME)):
                    time = FCST_TIME[i]
                    aqm_timestep = pd.to_datetime(time, format="%Y%m%d%H") - pd.Timedelta(hours=int(AQM_CYCLE))
                    if (time != FCST_TIME[0]) & (aqm_timestep.strftime("%H%M") == "0000"):
                        aqm_date = (aqm_timestep - pd.Timedelta(days=1)).strftime("%Y%m%d")
                        aqm_hour = "24"
                    else:
                        aqm_date = aqm_timestep.strftime("%Y%m%d")
                        aqm_hour = aqm_timestep.strftime("%H")
            
                    dyn_file = f"{EMI_PATH}/aqm.{aqm_date}/{AQM_CYCLE}/dynf0{aqm_hour}.nc"
                    print(f"Read LBC from {dyn_file}")
    
                    bc = aqm_loader(dyn_file, dynlist[idx])
                    bc = np.squeeze(bc[0, FCST_LAYER - 1, :, :])
                    if species == "OZONE":
                        bc = bc / 1000
    
                    top[i] = bc[0, :]  # top
                    bottom[i] = bc[-1, :]  # bottom
                    left[i] = bc[:, 0]  # left
                    right[i] = bc[:, -1]  # right
                    del [time, aqm_date, aqm_hour, dyn_file, bc]

            elif BNDY_OPTION == "fcst":
                halo = 0  # inner layer
                bndy_hour = np.arange(0, len(FCST_TIME), BNDY_LENGTH)
                bndy_path = f"{EMI_PATH}/aqm.{init_date}/{AQM_CYCLE}"

                pm25ac = aqm_loader(init_file, "pm25ac")
                pm25ac = np.squeeze(pm25ac[FCST_LAYER, :, :])
                pm25co = aqm_loader(init_file, "pm25co")
                pm25co = np.squeeze(pm25co[FCST_LAYER, :, :])

                for i in range(len(bndy_hour)):
                    bndy_file = f"{bndy_path}/aqm.t{AQM_CYCLE}z.gfs_bndy.tile7.f{bndy_hour[i]:03d}.nc"
                    print(f"Read LBC from {bndy_file}")
                    top0, bottom0, left0, right0 = aqm_bndy_loader(bndy_file, varlist[idx], FCST_LAYER, halo, pm25ac, pm25co)
                    top[bndy_hour[i]:bndy_hour[i]+BNDY_LENGTH] = [top0]*BNDY_LENGTH
                    bottom[bndy_hour[i]:bndy_hour[i]+BNDY_LENGTH] = [bottom0]*BNDY_LENGTH
                    left[bndy_hour[i]:bndy_hour[i]+BNDY_LENGTH] = [left0]*BNDY_LENGTH
                    right[bndy_hour[i]:bndy_hour[i]+BNDY_LENGTH] = [right0]*BNDY_LENGTH
                    del [top0, bottom0, left0, right0]

            else:
                print(f"LBC mode is not identified. Terminated")
                sys.exit(1)

            top = (np.stack(top, 0) - offset[idx]) / scaler[idx]
            bottom = (np.stack(bottom, 0) - offset[idx]) / scaler[idx]
            left = (np.stack(left, 0) - offset[idx]) / scaler[idx]
            right = (np.stack(right, 0) - offset[idx]) / scaler[idx]

            top = top[:len(FCST_TIME), :]
            bottom = bottom[:len(FCST_TIME), :]
            left = left[:len(FCST_TIME), :]
            right = right[:len(FCST_TIME), :]

            total_top += [np.expand_dims(top, 1)]
            total_bottom += [np.expand_dims(bottom, 1)]
            total_left += [np.expand_dims(left, 1)]
            total_right += [np.expand_dims(right, 1)]
            print(f'{species} lbc', pd.Timestamp("now"))
        total_top = np.concatenate(total_top, 1)
        total_bottom = np.concatenate(total_bottom, 1)
        total_left = np.concatenate(total_left, 1)
        total_right = np.concatenate(total_right, 1)
        print('lbc', total_top.shape, total_bottom.shape, total_left.shape, total_right.shape, pd.Timestamp("now"))
        return [total_top, total_bottom, total_left, total_right]


    def read_obs_fields(self, EMI_PATH, AQM_CYCLE, FCST_TIME, REGRIDDED_OBS, FCST_SPECIES, FCST_LAYER, ROLLBACK=24):
        varlist = ["NO2", "NH3", "HCHO", "OZONE", "PM25"]
        aqm_varlist = ["no2", "nh3", "form", "o3", "pm25_tot"]
        scaler = [ 1e-2, 1e-2, 1e-2, 1e-2,   10]
        offset = [    0,    0,    0,    0,    0]

        # ic
        init_date = (pd.to_datetime(FCST_TIME[0], format="%Y%m%d%H") - pd.Timedelta(hours=int(AQM_CYCLE))).strftime("%Y%m%d")
        init_file = f"{EMI_PATH}/aqm.{init_date}/{AQM_CYCLE}/aqm.t{AQM_CYCLE}z.gfs_data.tile7.halo0.nc"
        print(f"Read IC from {init_file}")

        ds = xr.open_dataset(REGRIDDED_OBS)

        total_data = []
        for species in FCST_SPECIES:
            try:
                idx = varlist.index(species)
                # ic
                ic = aqm_loader(init_file, aqm_varlist[idx])
                ic = np.squeeze(ic[FCST_LAYER, :, :])
                ic = np.repeat(np.expand_dims(ic, axis=0), ROLLBACK, axis=0)

                # obs
                obs = ds[species].data

                # merged ic
                data = np.where(obs > 0, ic, 0)
                mask = (data > 0).astype(float)
                data = (data - offset[idx]) / scaler[idx]
                data = np.append(np.expand_dims(data, axis=1), np.expand_dims(mask, axis=1), axis=1)
                total_data += [data]
                print(f'{species} obs', data.shape, pd.Timestamp("now"))
            except Exception as e:
                print(f"Surface obs loading error: {e}")

        ds.close()
        total_data = np.concatenate(total_data, 1)
        print('obs', total_data.shape, pd.Timestamp("now"))
        return total_data


    def save_restart(self, FCST_TIME, INPUT_DATA, FCST_SPECIES, FCST_LAYER, OUTPUT_PATH):
        fcst_hour = np.arange(len(FCST_TIME))
        rollback_hour = np.arange(-1*24, 0)
        grid_yt = np.arange(INPUT_DATA[0].shape[2]) + 1
        grid_xt = np.arange(INPUT_DATA[0].shape[3]) + 1

        sat_variable = ["aod", "no2"]  # full list: "aod", "no2", "o3_avg", "co"
        sat_variable = [item for x in sat_variable for item in (x, f"{x}_mask")]
        static_variable = ["grid_latt", "grid_lont", "area", "zsurf", "land"]
        met_variable = ["ugrd10m", "vgrd10m", "hpbl", "spfh2m", "dswrf_ave", \
                       "tmp2m", "veg", "tcdc_aveclm", "tprcp", "lhtfl_ave", \
                       "fricv", "pressfc", "cnwat", "snowc_ave"]
        fcst_variable = FCST_SPECIES
        fcst_variable_ext = [item for x in fcst_variable for item in (x, f"{x}_mask")]

        output_file = f"{OUTPUT_PATH}/deepaqm_restart_layer{FCST_LAYER}_f{(len(FCST_TIME)-1):03d}.nc"

        ds = xr.Dataset(
            coords={
                "static_time": ("static_time", [fcst_hour[0]]),
                "met_time": ("met_time", fcst_hour[1:]),
                "fcst_time": ("fcst_time", fcst_hour),
                "rollback_time": ("rollback_time", rollback_hour),
                "yt": ("grid_yt", grid_yt),
                "xt": ("grid_xt", grid_xt),
                "sat_variable": ("sat_variable", sat_variable),
                "static_variable": ("static_variable", static_variable),
                "met_variable": ("met_variable", met_variable),
                "fcst_variable": ("fcst_variable", fcst_variable_ext),
                "fcst_variable_bndy": ("fcst_variable_bndy", fcst_variable)
            }
        )
    
        ds["time_utc"] = xr.DataArray(FCST_TIME, dims=["fcst_time"], coords=[fcst_hour])
        ds["sat"] = xr.DataArray(INPUT_DATA[0], dims=["static_time", "sat_variable", "yt", "xt"], coords=[[fcst_hour[0]], sat_variable, grid_yt, grid_xt])
        ds["static"] = xr.DataArray(INPUT_DATA[1], dims=["static_time", "static_variable", "yt", "xt"], coords=[[fcst_hour[0]], static_variable, grid_yt, grid_xt])
        ds["met"] = xr.DataArray(INPUT_DATA[2], dims=["met_time", "met_variable", "yt", "xt"], coords=[fcst_hour[1:], met_variable, grid_yt, grid_xt])
        ds["fcst_species"] = xr.DataArray(INPUT_DATA[3], dims=["rollback_time", "fcst_variable", "yt", "xt"], coords=[rollback_hour, fcst_variable_ext, grid_yt, grid_xt])
        ds["bndy_top"] = xr.DataArray(INPUT_DATA[4][0], dims=["fcst_time", "fcst_variable_bndy", "xt"], coords=[fcst_hour, fcst_variable, grid_xt])
        ds["bndy_bottom"] = xr.DataArray(INPUT_DATA[4][1], dims=["fcst_time", "fcst_variable_bndy", "xt"], coords=[fcst_hour, fcst_variable, grid_xt])
        ds["bndy_left"] = xr.DataArray(INPUT_DATA[4][2], dims=["fcst_time", "fcst_variable_bndy", "yt"], coords=[fcst_hour, fcst_variable, grid_yt])
        ds["bndy_right"] = xr.DataArray(INPUT_DATA[4][3], dims=["fcst_time", "fcst_variable_bndy", "yt"], coords=[fcst_hour, fcst_variable, grid_yt])

        ds["sat"].attrs["description"] = sat_variable
        ds["static"].attrs["description"] = static_variable
        ds["met"].attrs["description"] = met_variable
        ds["fcst_species"].attrs["description"] = fcst_variable_ext
        ds["bndy_top"].attrs["description"] = fcst_variable
        ds["bndy_bottom"].attrs["description"] = fcst_variable
        ds["bndy_left"].attrs["description"] = fcst_variable
        ds["bndy_right"].attrs["description"] = fcst_variable

        ds.to_netcdf(output_file)
        print(f"Restart file saved to {output_file}")
    
    
    def main_driver(self, TEMPO_NO2_MASK=False):
        start_time = pd.Timestamp("now")
    
        AQM_DATE, AQM_CYCLE, MET_OPTION, MET_PATH, AQM_PATH, EMI_PATH, VIIRS_PATH, TEMPO_PATH, OBS_PATH, OUTPUT_PATH, FCST_LENGTH, BNDY_LENGTH, FCST_SPECIES, FCST_LAYER, BNDY_OPTION, RESTART = self.namelist_config()
    
        if RESTART:
            RESTART_FILE = f"{OUTPUT_PATH}/deepaqm_restart_layer{FCST_LAYER}_f{FCST_LENGTH:03d}.nc"
            print(f"Reading input data from restart file {RESTART_FILE}")
            STATIC = aqm_loader(RESTART_FILE, "static")
            MET = aqm_loader(RESTART_FILE, "met")
            SAT = aqm_loader(RESTART_FILE, "sat")
            OBS = aqm_loader(RESTART_FILE, "fcst_species")
            LBC = [
                aqm_loader(RESTART_FILE, "bndy_top"),
                aqm_loader(RESTART_FILE, "bndy_bottom"),
                aqm_loader(RESTART_FILE, "bndy_left"),
                aqm_loader(RESTART_FILE, "bndy_right")
            ]
        else:
            print("Reading input data from initial AQM files...")
            FCST_TIME = pd.date_range(
                start=pd.to_datetime(AQM_DATE + AQM_CYCLE, format="%Y%m%d%H"),
                periods=FCST_LENGTH + 1,
                freq="h"
            ).strftime("%Y%m%d%H")


            print("Processing satellite/surface observation...")
            REGRIDDED_VIIRS = f"{OUTPUT_PATH}/regridded_viirs.nc"
            REGRIDDED_TEMPO = f"{OUTPUT_PATH}/regridded_tempo.nc"
            REGRIDDED_OBS = f"{OUTPUT_PATH}/regridded_obs.nc"

            if os.path.exists(REGRIDDED_VIIRS):
                print(f"Regridded viirs file exists: {REGRIDDED_VIIRS}")
            else:
                satfiles = glob.glob(f"{VIIRS_PATH}/viirs_eps_*_aod_0.100_deg_{AQM_DATE}_nrt.nc")
                satfiles = np.sort(satfiles)
                regridder = sat2aqm_regridder()
                regridder.viirs_regridder(satfiles, OUTPUT_PATH, REGRIDDED_VIIRS, AQM_DATE + AQM_CYCLE)

            if os.path.exists(REGRIDDED_TEMPO):
                print(f"Regridded tempo file exists: {REGRIDDED_TEMPO}")
            else:
                satfiles = glob.glob(f"{TEMPO_PATH}/TEMPO_NO2_L3_*_{AQM_DATE}*.nc")
                satfiles = np.sort(satfiles)
                regridder = sat2aqm_regridder()
                regridder.tempo_regridder(satfiles, OUTPUT_PATH, REGRIDDED_TEMPO, AQM_DATE + AQM_CYCLE)

            if os.path.exists(REGRIDDED_OBS):
                print(f"Regridded surface obs file exists: {REGRIDDED_OBS}")
            else:
                regridder = airnow2aqm_regridder()
                regridder.regridder(OBS_PATH, OUTPUT_PATH, REGRIDDED_OBS, AQM_DATE + AQM_CYCLE)

            # The order of regridded satellite files should be ["aod", "no2", "o3_avg", "co"].
            # Currently only "aod" and "no2" are used.    
            STATIC = self.read_static_fields(f"{AQM_PATH}/{AQM_DATE}{AQM_CYCLE}")
            MET = self.read_met_fields(MET_OPTION, MET_PATH, AQM_DATE, AQM_CYCLE, FCST_TIME[1:])
            SAT = self.read_sat_fields([REGRIDDED_VIIRS, REGRIDDED_TEMPO])
            OBS = self.read_obs_fields(EMI_PATH, AQM_CYCLE, FCST_TIME, REGRIDDED_OBS, FCST_SPECIES, FCST_LAYER)
            LBC = self.read_lbc_fields(EMI_PATH, AQM_CYCLE, FCST_TIME, BNDY_LENGTH, FCST_SPECIES, FCST_LAYER, BNDY_OPTION)
            self.save_restart(FCST_TIME, (SAT, STATIC, MET, OBS, LBC), FCST_SPECIES, FCST_LAYER, OUTPUT_PATH)
            sys.exit(1)

        # remove tempo no2 with cloud cover 100%
        if TEMPO_NO2_MASK:                
            mask = MET[0, 7, :, :] == 1  # tcdc_aveclm
            SAT[0, 2, mask] = 0   # no2
            SAT[0, 3, mask] = 0   # no2 mask

        #SAT[0, 0, :] = 0
        #SAT[0, 1, :] = 0
        SAT[:] = 0
        OBS[:] = 0

        # Input shape = (batch, time, channel, height, width)
        STATIC = np.expand_dims(STATIC, 0)
        MET = np.expand_dims(MET, 0)
        SAT = np.expand_dims(SAT, 0)
        OBS = np.expand_dims(OBS, 0)

        self.data_set = (SAT, STATIC, MET, OBS)
        self.lbc = LBC
