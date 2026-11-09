
import sys, yaml
from jinja2 import Environment, FileSystemLoader

# Read arguments from command line
init_time = sys.argv[1]
aqm_date = init_time[:8]
aqm_cycle = init_time[8:]
print(aqm_date)

# Set up jinja2 environment
env = Environment(loader=FileSystemLoader(searchpath="."))

# Read template, render configs from arguments, and create namelist
template = env.get_template("namelist.template")

configs = {
    "aqm_date": aqm_date,
    "aqm_cycle": aqm_cycle,
    "fcst_length": 72,
    "bndy_length": 6,
    "fcst_layer": 64,
    "model_mode": 0,
    "met_option": "gfs",
    "bndy_option": "fcst",
    "no2": False,
    "nh3": False,
    "hcho": False,
    "ozone": True,
    "pm25": True,
    "restart": False,
    "output_path": "/scratch4/NCEPDEV/naqfc/Wei-ting.Hung/deepaqm/output",
    "met_path": "/scratch3/NCEPDEV/stmp/Youhua.Tang/gfs-sfc",
    "aqm_path": "/scratch3/NCEPDEV/stmp/Youhua.Tang/naqfc-data",
    "emi_path": "/scratch3/NCEPDEV/stmp/Youhua.Tang/naqfc-data",
    "viirs_path": "/scratch4/NCEPDEV/naqfc/Wei-ting.Hung/ALLDATA/viirs",
    "tempo_path": "/scratch4/NCEPDEV/naqfc/Wei-ting.Hung/ALLDATA/tempo",
    "obs_path": "/scratch4/NCEPDEV/naqfc/Wei-ting.Hung/ALLDATA/airnow",
    "no2_model_path": None,
    "nh3_model_path": None,
    "hcho_model_path": None,
    "ozone_model_path":"./models/fcst_ozone_model.pth",
    "pm25_model_path": "./models/fcst_pm25_model.pth",
    "no2_fusion_path": None,
    "nh3_fusion_path": None,
    "hcho_fusion_path": None,
    "ozone_fusion_path": None,
    "pm25_fusion_path": None
}

with open(f"namelist", "w") as f:
    f.write(template.render(**configs))
