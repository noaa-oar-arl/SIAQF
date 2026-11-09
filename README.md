# SIAQF
Super Intelligence-based model to provide air quality forecasting.

The repository provide the research-to-operation transition for implementing the UFS-DeepAQM, which uses UFS-AQM's inputs to makes air quality forecasting.

Current UFS-DeepAQM has two model modes: Base and Fusion modes.
The Base mode uses the benchmark version of UFS-DeepAQM, emulator of UFS-AQMv8 that purely based on UFS-AQM's initial and boundary conditions. The Fusion mode creates fused initial condision from UFS-AQM products and satellite and surface observations, then generates air quality forecast based on fused fields.

### Namelist options
The UFS-AQM run used as input sources, forecasting period and chmiecal species, and input and output directories can be specified in the namelist. Five chmiecal species (NO2, NH3, HCHO, O3 and PM2.5) are set as default, but currently only O3 and PM2.5 are available (updated on Feb 25 2026).

| Option           | Description                                             |
| ---------------- | ------------------------------------------------------- |
| AQM_DATE         | Date of UFS-AQM run, format=YYYYMMDD                    |
| AQM_CYCLE        | Time cycle of UFS-AQM run, format=HH                    |
| FCST_LENGTH      | Length of forecast timestep, unit=hour                  |
| BNDY_LENGTH      | Time interval of UFS-AQM boundary conditions, unit=hour |
| FCST_LAYER       | The UFS-AQM vertical layer where forecasting chmiecal species at. FCST_LAYER=64 represents the surface based on UFS-AQM configuration. |
| MODEL_MODE       | 0: Base mode; 1: Fusion mode                            |
| MET_OPTION       | Source of met data (GFS/AQM)                            |
| BNDY_OPTION      | Source of LBC data (retro/fcst). For retro, LBC will be generated from AQM dyn outputs. For fcst, LBC will be loaded from AQM LBC files. |
| NO2              | Option to run NO2 forecasting (True/False)              |
| NH3              | Option to run NH3 forecasting (True/False)              |
| HCHO             | Option to run HCHO forecasting (True/False)             |
| OZONE            | Option to run O3 forecasting (True/False)               |
| PM25             | Option to run PM2.5 forecasting (True/False)            |
| RESTART          | Option to use generated restart file instead of collecting inputs from UFS-AQM run (True/False). When `RESTART=Flase`, the input generator will read and process inputs from the specified UFS-AQM run. All processed inputs will be saved in a restart file. When `RESTART=True`, the model driver will directly read inputs from the restart file and the input processes will NOT be triggered. |
| OUTPUT_PATH      | Path of the work/output directory. A subdirectory based on AQM_DATE and AQM_CYLCE will be created under this path.               |
| AQM_PATH         | Path of UFS_AQM runs. The input generator will search for the subdirectory based on AQM_DATE and AQM_CYLCE under this path.      |
| EMI_PATH         | Path of UFS_AQM emissions and IC/BC. The input generator will search for the subdirectory based on AQM_DATE and AQM_CYLCE under this path. |
| VIIRS_PATH       | Path of VIIRS AOD products. The input generator will search for files based on AQM_DATE under this path. Required for FUSION MODE only.    |
| TEMPO_PATH       | Path of TEMPO NO2 products. The input generator will search for files based on AQM_DATE under this path. Required for FUSION MODE only.    |
| OBS_PATH         | Path of suface monitoring products (AirNow dy default). The input generator will search for files based on AQM_DATE and AQM_CYLCE under this path. Required for FUSION MODE only. |
| NO2_MODEL_PATH   | Path of NO2 forecast model. Use `None` if no model avlable.   |
| NH3_MODEL_PATH   | Path of NH3 forecast model. Use `None` if no model avlable.   |
| HCHO_MODEL_PATH  | Path of HCHO forecast model. Use `None` if no model avlable.  |
| OZONE_MODEL_PATH | Path of OZONE forecast model. Use `None` if no model avlable. |
| PM25_MODEL_PATH  | Path of PM25 forecast model. Use `None` if no model avlable.  |
| NO2_FUSION_PATH  | Path of NO2 fusion-ic model. Use `None` if no model avlable. Required for FUSION MODE only.   |
| NH3_FUSION_PATH  | Path of NH3 fusion-ic model. Use `None` if no model avlable. Required for FUSION MODE only.   |
| HCHO_FUSION_PATH | Path of HCHO fusion-ic model. Use `None` if no model avlable.Required for FUSION MODE only.   |
| OZONE_FUSION_PATH| Path of OZONE fusion-ic model. Use `None` if no model avlable. Required for FUSION MODE only. |
| PM25_FUSION_PATH | Path of PM25 fusion-ic model. Use `None` if no model avlable. Required for FUSION MODE only.  |

### Required inputs
## UFS-AQM
| Application                          | Filename                                                            |
| ------------------------------------ | ------------------------------------------------------------------- |
| Model Coordinate / land properties   | `grid_spec.nc` `atmos_static.nc` (included in `fix/`)               |
| Meteorology                          | Operational GFS or `phyf*.nc` from AQM                              |
| Emission                             | `aqm.t*z.NEXUS_Expt.nc`, `aqm.t*z.PT.nc`, `Hourly_Emissions_*.nc` |
| Initial/Boundary                     | `aqm.t*z.gfs_data.tile7.halo0.nc`, `aqm.t*z.gfs_bndy.tile7.f*.nc` |​

## Observations for fusion mode
| Dataset              | Filename                                                            |
| -------------------- | ------------------------------------------------------------------- |
| VIIRS AOD            | `viirs_eps_npp_aod_0.100_deg_*_nrt.nc` Can be downloaded from [NOAA/NESDIS/STAR](https://www.star.nesdis.noaa.gov/pub/smcd/VIIRS_Aerosol/viirs_aerosol_gridded_data/snpp/aod/eps/)                    |
| TEMPO NO2            | `TEMPO_NO2_L3_NRT_V02_*.nc`Can be downloaded from [EARTHDATA](https://www.earthdata.nasa.gov/data/instruments/tempo/data-access-tools)   |
| Surface measurements (Airnow by defalut)  | `HourlyAQObs_*.dat` Can be downloaded from [AirNow-Tech](https://files.airnowtech.org/)                             |

### Script description
## Primary workflow
| Filename             | Application                                                            |
| -------------------- | ---------------------------------------------------------------------- |
| `model_pred`         | Main driver, calling processes according to namelist                   |
| `model_input_gen`    | Input generator for Base mode                                          |
| `model_fusion_gen`   | Input generator for Fusion mode                                        |
| `namelist_gen`       | Namelist generator. Optional, mainly used for multiple forecast cycle  |

## Toolkit
| Filename               | Application                                                         |
| ---------------------- | ------------------------------------------------------------------- |
| `aqm_loaders`          | Data loader of UFS-AQM fields (air quality, meteorology, emissions, initial/boundary conditions)  |
| `gfs_loaders`          | Data loader of GFS meteorology, available for NetCDF and grib2 formats (NetCDF by default)        |
| `obs_loaders`          | Data loader of satellite/surface observations. Available options: VIIRS, TEMPO, AirNow, AQS       |
| `gfs2aqm_regridder`    | Regridding GFS fields to UFS-AQM coordinate                         |
| `sat2aqm_regridder`    | Regridding satellite products to UFS-AQM coordinate                 |
| `airnow2aqm_regridder` | Regridding AirNow products to UFS-AQM coordinate                    |
| `pt2aqm_grid_gen`      | Generator of grid index based on UFS-AQM coordinate for quick plume emission mapping, required when changing emission versions (e.g. UFS-AQMv8 -> v7). This script is not included in the forecast workflow and should be called before running the workflow.               |

### Run the models
ML models are running parallelly in `model_pred.py`. 

[Update on Aug 26 2026] Parallel process is currently disabled for GPU. See line 108-120 in `model_pred.py`.

On GMU Hopper (1 node 12 core), the input generation process takes ~ 4 min and ML models take ~ 13 min to complete 72 h forecast for two chemical species. Recommended slurm settings to run 72 h forecast for two chemical species on Hopper:
```
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=12
#SBATCH --mem=72G
#SBATCH --time=0-00:20:00
```
On NOAA Gaea C6 (1 node 2 core), the input generation process takes ~ 6 min and ML models take ~ 2 min to complete 72 h forecast for two chemical species. Recommended slurm settings to run 72 h forecast for two chemical species on Gaea C6:
```
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=2
#SBATCH --time=0-00:10:00
```
On NOAA Ursa, if running on CPU (1 node 20 core), the input generation process takes ~ 11 min and ML models take ~ 1 hour to complete 72 h forecast for two chemical species. If running forecasting on 1 GPU, ML models take ~ 2 min to complete 72 h forecast for two chemical species. Recommended slurm settings to run 72 h forecast for two chemical species on Ursa:

[CPU]
```
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=20
#SBATCH --time=0-01:20:00
```
[GPU]
```
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=20
#SBATCH --gpus=h100:1
#SBATCH --time=0-00:20:00
```

### ML model version log
| Date        | Version (species_version#_epoch)       |
| ----------- | -------------------------------------- |
| Feb 18 2026 | (Base) pm25_l1_19, ozone_l2_19         |
| Nov 9 2026  | (Fusion-ic) pm25_k4_8, ozone_l41_7 (Fusion-fcst) pm25_aa93_17, ozone_bb93_17   |
