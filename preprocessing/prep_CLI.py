<<<<<<< HEAD
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
=======
#!/usr/bin/env python
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
from netCDF4 import Dataset
from datetime import datetime
import math
import os, glob
import matplotlib.pyplot as plt
from defParam import parameters
par = parameters()
from COORD_AC import MERRA2_GEOreference
crds = MERRA2_GEOreference()

np.warnings.filterwarnings('ignore')
#env_keep += "XDG_RUNTIME_DIR"

'''===================================================================================================================
Creates climates files
Note: the extraction of the meteorological forcings will depend on the source.
Here for 2011 through 2016
======================================================================================================================'''

def run_cli_ts(VAR_lat, VAR_lon,latini, lonini, st_lat,st_lon):
    #INPUT BY USER
    start_date = '2011-01-01'
    end_date = '2016-12-31'
    Freq = 1                            #1=daily, 2=10-daily, 3=monthly
    years =['Y2011', 'Y2012', 'Y2013','Y2014', 'Y2015','Y2016']
    months = ['M01', 'M02', 'M03','M04','M05','M06','M07','M08','M09','M10','M11','M12']

    #Convert variables to lat lon
    latpt = crds.M2AC_row_to_lat(VAR_lat)
    lonpt  =crds.M2AC_col_to_lon(VAR_lon)


    name_dir = '/my_dir/CLI_files/' + str(VAR_lat) + '_' + str(VAR_lon) + '_2011-2016'
    name = str(round(latpt,2)) + '_' + str(round(lonpt,3)) + '_'
    name_fil = str(VAR_lat) + '_' + str(VAR_lon)+ '_'
    os.mkdir(name_dir)

    #Define minimum distance function for coordinate matching
    def mindist(point, array):
        mindist = np.abs(array - point).argmin()
        return mindist

    # Only run for grid-cells on land  # Need cleaner method
    lat_id, lon_id = mindist(latpt, lats), mindist(lonpt, lons)

    # Create DataFrames for data ouput METEO
    date_s = datetime.strptime(start_date, '%Y-%m-%d').date()
    date_e = datetime.strptime(end_date, '%Y-%m-%d').date()
    TMP = pd.DataFrame(columns=['TSmin', 'TSmax'], index=pd.date_range(date_s, date_e))
    PLU = pd.DataFrame(columns=['PLU'], index=pd.date_range(date_s, date_e))
    ETo = pd.DataFrame(columns=['ETo'], index=pd.date_range(date_s, date_e))

    # Loop over files
    # EXTRACT METEO FORCING FROM SOURCE AND FILL TMP, PLU, ETo
    #....


    # write output files
    title = name + '- daily data:' + start_date + ' to ' + end_date
    head_date = '\n'.join([title,
                            '     ' + str(Freq) + '  : Daily records (1=daily, 2=10-daily and 3=monthly data)',
                            '     ' + str(
                            date_s.day) + '  : First day of record (1, 11 or 21 for 10-day or 1 for months)',
                            '     ' + str(date_s.month) + '  : First month of record',
                            '  ' + str(
                            date_s.year) + '  : First year of record (1901 if not linked to a specific year)'
                                                  '\n'])

    hd_tmp = '''Tmin (C)   Tmax (C)\n======================'''
    head_tmp = '\n'.join([head_date, hd_tmp])
    tmp_fn = name_fil + '.Tnx'

    hd_prec = ''' Total Rain (mm)\n======================='''
    head_prec = '\n'.join([head_date, hd_prec])
    prec_fn = name_fil + '.PLU'

    hd_ETo = '''  Average ETo (mm/day)\n======================='''
    head_ETo = '\n'.join([head_date, hd_ETo])
    eto_fn = name_fil + '.ETo'

    np.savetxt(name_dir + tmp_fn, TMP, fmt=('%3.1f', '%3.1f'), comments='', header=head_tmp, delimiter='\t')
    np.savetxt(name_dir + prec_fn, PLU, fmt='%3.1f', comments='', header=head_prec)
    np.savetxt(name_dir + eto_fn, ETo, fmt='%3.1f', comments='', header=head_ETo)
    climate = (open(name_dir + name_fil + '.CLI', 'w')).write('\n'.join([title,
                                                        ' 7.1   : AquaCrop Version (August 2023)',
                                                        tmp_fn,
                                                        eto_fn,
                                                        prec_fn,'MaunaLoa.CO2']))
>>>>>>> 1c54a49aa9ee900dca1fb006f34c905955f94616
