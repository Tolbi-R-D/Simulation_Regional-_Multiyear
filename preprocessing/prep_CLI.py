#!/usr/bin/env python
import xarray as xr
import numpy as np
import pandas as pd
import os
from datetime import datetime
import warnings

# Import de votre classe de référence (supposée être dans COORD.py ou définie au-dessus)
# de Roos et al. (2021)
class MERRA2_GEOreference():
    def __init__(self, ):
        self.M2AC_ini_lat = 60
        self.M2AC_ini_lon = -10.625
        self.M2AC_step_lat = 0.5
        self.M2AC_step_lon = 0.625
        self.CLI_latrange=np.arange(self.M2AC_ini_lat, 30, -self.M2AC_step_lat)
        self.CLI_lonrange=np.arange(self.M2AC_ini_lon, 45.625, self.M2AC_step_lon)
    def M2AC_row_to_lat(self, row):
        return self.M2AC_ini_lat - (row * self.M2AC_step_lat)
    def M2AC_col_to_lon(self, col):
        return self.M2AC_ini_lon + (col * self.M2AC_step_lon)

crds = MERRA2_GEOreference()
warnings.filterwarnings('ignore')

def run_cli_ts(VAR_lat, VAR_lon, path_to_merra_files):
    # 1. PARAMÈTRES
    start_date = '2011-01-01'
    end_date = '2016-12-31'
    Freq = 1 # Quotidien
    
    # Conversion indices -> coordonnées
    latpt = crds.M2AC_row_to_lat(VAR_lat)
    lonpt = crds.M2AC_col_to_lon(VAR_lon)
    print(f"Extraction pour : Lat {latpt}, Lon {lonpt}")

    # Création du dossier de sortie
    name_dir = os.path.join(os.getcwd(), f'CLI_files/{VAR_lat}_{VAR_lon}')
    os.makedirs(name_dir, exist_ok=True)

    # 2. EXTRACTION DES DONNÉES (CORRECTION ICI)
    try:
        # On ouvre les fichiers NetCDF (adapter le pattern *.nc)
        ds = xr.open_mfdataset(path_to_merra_files, combine='by_coords')
        
        # Sélection spatiale et temporelle
        # On cherche la valeur la plus proche (method='nearest')
        data_pixel = ds.sel(lat=latpt, lon=lonpt, method='nearest').sel(time=slice(start_date, end_date))
        
        # Conversion des unités MERRA-2 -> AquaCrop
        # Temp: Kelvin to Celsius
        tmax = data_pixel['T2MMAX'].values - 273.15
        tmin = data_pixel['T2MMIN'].values - 273.15
        # Precip: kg/m2/s to mm/day (86400 sec dans un jour)
        precip = data_pixel['PRECTOTCORR'].values * 86400
        # ETo: Si MERRA-2 n'a pas d'ETo, on utilise une valeur par défaut ou un calcul
        # Ici, on extrait si dispo, sinon calcul simplifié ou 0.0
        eto = data_pixel['EVAP'].values * 86400 if 'EVAP' in data_pixel else np.full_like(tmax, 4.0)

    except Exception as e:
        print(f"Erreur lors de la lecture des fichiers : {e}")
        return

    # 3. CRÉATION DES DATAFRAMES AVEC LES VALEURS RÉELLES
    date_range = pd.date_range(start_date, end_date)
    TMP = pd.DataFrame({'TSmin': tmin, 'TSmax': tmax}, index=date_range)
    PLU = pd.DataFrame({'PLU': precip}, index=date_range)
    ETo = pd.DataFrame({'ETo': eto}, index=date_range)

    # 4. ÉCRITURE DES FICHIERS (Format strict AquaCrop)
    name_fil = f"{VAR_lat}_{VAR_lon}_"
    date_s = datetime.strptime(start_date, '%Y-%m-%d')
    
    title = f"Data {latpt}_{lonpt} : {start_date} to {end_date}"
    header_base = f"{title}\n {Freq} : Daily\n {date_s.day} : First day\n {date_s.month} : First month\n {date_s.year} : First year\n"

    # Sauvegarde .Tnx
    tmp_fn = name_fil + '.Tnx'
    with open(os.path.join(name_dir, tmp_fn), 'w') as f:
        f.write(header_base + "Tmin (C)   Tmax (C)\n======================\n")
        np.savetxt(f, TMP.values, fmt='%3.1f\t%3.1f')

    # Sauvegarde .PLU
    prec_fn = name_fil + '.PLU'
    with open(os.path.join(name_dir, prec_fn), 'w') as f:
        f.write(header_base + " Total Rain (mm)\n=======================\n")
        np.savetxt(f, PLU.values, fmt='%3.1f')

    # Sauvegarde .ETo
    eto_fn = name_fil + '.ETo'
    with open(os.path.join(name_dir, eto_fn), 'w') as f:
        f.write(header_base + " Average ETo (mm/day)\n=======================\n")
        np.savetxt(f, ETo.values, fmt='%3.1f')

    # Fichier .CLI
    cli_path = os.path.join(name_dir, name_fil + '.CLI')
    with open(cli_path, 'w') as f:
        f.write(f"{title}\n 7.1 : AquaCrop Version\n{tmp_fn}\n{eto_fn}\n{prec_fn}\nMaunaLoa.CO2")
    
    print(f"Succès ! Fichiers générés dans {name_dir}")

if __name__ == "__main__":
    # MODIFIEZ LE CHEMIN CI-DESSOUS vers vos fichiers .nc
    PATH_DATA = "chemin/vers/vos/fichiers/*.nc" 
    run_cli_ts(53, 20, PATH_DATA)