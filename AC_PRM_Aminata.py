#!/usr/bin/env python
import numpy as np
import os
from datetime import datetime

def run_ac_pro_yrs(site_name, cluster_name, soil_name, DIR_OUT_ROOT, DirSoil, DirCli, DirCrop, DirSuppfiles, start_year, end_year):
    fname = cluster_name
    
    # Chemins Windows robustes avec guillemets
    DirSoil_f = f'   "{os.path.abspath(DirSoil)}' + os.sep + '"\n'
    DirCrop_f = f'   "{os.path.abspath(DirCrop)}' + os.sep + '"\n'
    DirSupp_f = f'   "{os.path.abspath(DirSuppfiles)}' + os.sep + '"\n'
    Dir_cli_site = os.path.join(DirCli, site_name)
    Dir_cli_f = f'   "{os.path.abspath(Dir_cli_site)}' + os.sep + '"\n'
    
    CROfile, IRRfile, MANfile = 'Mastrop143', 'Inet_50RAW', 'SFR30'

    prm_path = os.path.join('LIST', f"{fname}.PRM")
    
    with open(prm_path, 'w') as fid:
        years = np.arange(start_year, end_year + 1)
        sim_s = [f"{y}-07-01" for y in years]
        sim_e = [f"{y}-12-31" for y in years]

        # AJOUTEZ CETTE LIGNE POUR AFFICHER LE NOMBRE DE CYCLES
        #print(f"Nombre de cycles pour {cluster_name} : {len(sim_s)}")
        
        fid.write(f"{fname}\n")
        fid.write('\t 7.1\t\t: AquaCrop Version (August 2023)\n')
        fid.write(f'\t {len(sim_s)}\n')

        def to_ac(d_str):
            s = datetime.strptime(d_str, '%Y-%m-%d')
            m_ref = [0, 0, 31, 59.25, 90.25, 120.25, 151.25, 181.25, 212.25, 243.25, 273.25, 304.25, 334.25]
            return int((s.year - 1901) * 365.25 + m_ref[s.month] + s.day)

        for n in range(len(sim_s)):
            ds, de = to_ac(sim_s[n]), to_ac(sim_e[n])
            if n > 0: fid.write('  1\n')
            len(sim_s)
            fid.writelines([
                f'\t {ds}\t\t: First day simulation\n',
                f'\t {de}\t\t: Last day simulation\n',
                f'\t {ds}\t\t: First day crop\n',
                f'\t {de}\t\t: Last day crop\n'
            ])

            fid.writelines(['-- 1. Climate (CLI) file\n',
                            f'   {cluster_name}.CLI\n', Dir_cli_f,
                            '   1.1 Temperature (TNx or TMP) file\n',
                            f'   {cluster_name}.Tnx\n', Dir_cli_f,
                            '   1.2 Reference ET (ETo) file\n',
                            f'   {cluster_name}.ETo\n', Dir_cli_f,
                            '   1.3 Rain (PLU) file\n', f'   {cluster_name}.PLU\n', Dir_cli_f,
                            '   1.4 Atmospheric CO2 concentration (CO2) file\n',
                            '   MaunaLoa.CO2\n',
                            '   ".\\SIMUL\\"\n'])
            
            fid.writelines(['-- 2. Calendar file\n', '   (None)\n', '   (None)\n',
                            '-- 3. CROP (CRO) file\n', f'   {CROfile}.CRO\n', DirCrop_f,
                            '- 4. Irrigation management (IRR) file\n', f'   {IRRfile}.IRR\n', DirSupp_f,
                            '-- 5. Field management (MAN) file\n', f'   {MANfile}.MAN\n', DirSupp_f,
                            '-- 6. Soil profile (SOL) file\n', f'   {soil_name}.SOL\n', DirSoil_f,
                            '-- 7. Groundwater table (GWT) fileT\n', '   (None)\n', '   (None)\n', 
                            '-- 8. Initial conditions (SW0) file\n', '   (None)\n', '   (None)\n',
                            '-- 9. Off-season conditions (OFF) file\n', '   (None)\n', '   (None)\n',
                            '10. Field data (OBS) file\n', '   (None)\n', '   (None)\n'
                            ])