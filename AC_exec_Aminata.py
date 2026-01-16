#!/usr/bin/env python
import os
import shutil
import subprocess
from AC_PRM_Aminata import run_ac_pro_yrs

AC_EXECUTABLE_NAME = 'aquacrop.exe' 
BASE_DIR = os.getcwd() 

INPUT_DIR = os.path.join(BASE_DIR, 'data_senegal', 'INPUT')
DIR_OUT_ROOT = os.path.join(BASE_DIR, 'data_senegal', 'OUTPUT')

DirSoil = os.path.join(INPUT_DIR, 'soil')
DirCli = os.path.join(INPUT_DIR, 'climate')
DirCrop = os.path.join(INPUT_DIR, 'crop')
DirSuppfiles = os.path.join(INPUT_DIR, 'suppl_input')
SIMUL_SOURCE = os.path.join(INPUT_DIR, 'SIMUL')
AC_SOURCE = os.path.abspath(os.path.join(BASE_DIR, 'aquacrop-7.1-x86_64-windows', AC_EXECUTABLE_NAME))

def main():
    if not os.path.exists(DIR_OUT_ROOT): os.makedirs(DIR_OUT_ROOT)
    
    sites = [d for d in os.listdir(DirCli) if os.path.isdir(os.path.join(DirCli, d))]
    soils = [s[:-4] for s in os.listdir(DirSoil) if s.lower().endswith('.sol')]
    
    for site in sites:
        site_path = os.path.join(DirCli, site)
        clusters = [f[:-4] for f in os.listdir(site_path) if f.lower().endswith('.cli')]

        for cluster in clusters:
            selected_soil = next((s for s in soils if s.lower() in cluster.lower()), soils[0] if soils else None)
            if selected_soil:
                wrapper(site, cluster, selected_soil, 2011, 2016)

def wrapper(site_name, cluster_name, soil_name, start_year, end_year):

    pa = os.path.join(DIR_OUT_ROOT, cluster_name)
    
    if os.path.exists(pa): shutil.rmtree(pa)
    os.makedirs(pa)
    os.chdir(pa) 
    
    # Préparation
    shutil.copytree(SIMUL_SOURCE, 'SIMUL')
    os.mkdir('OUTP')
    os.mkdir('LIST')
    
    with open('LIST/ListProjects.txt', 'w') as f:
        f.write(f"{cluster_name}.PRM\n")
    
    shutil.copyfile(AC_SOURCE, AC_EXECUTABLE_NAME)
    
    # Appel du PRM 
    run_ac_pro_yrs(site_name, cluster_name, soil_name, DIR_OUT_ROOT, 
                   DirSoil, DirCli, DirCrop, DirSuppfiles, 
                   start_year, end_year)
    
    try:
        # Exécution d'AquaCrop
        subprocess.run([AC_EXECUTABLE_NAME], capture_output=True)
        
        # --- RÉORGANISATION POUR RESSEMBLER À 0_0 ---
        
        # 1. Déplacer le fichier .PRM de LIST/ vers la racine du cluster
        prm_src = os.path.join('LIST', f"{cluster_name}.PRM")
        if os.path.exists(prm_src):
            shutil.move(prm_src, f"{cluster_name}.PRM")
        
        # 2. Supprimer les fichiers système inutiles dans OUTP/
        for log_file in ['AllDone.OUT', 'ListProjectsLoaded.OUT']:
            target = os.path.join('OUTP', log_file)
            if os.path.exists(target):
                os.remove(target)
        
        # 3. Supprimer les dossiers techniques et l'exécutable
        shutil.rmtree('LIST')
        shutil.rmtree('SIMUL')
        os.remove(AC_EXECUTABLE_NAME)
        
        print(f"TERMINÉ : {cluster_name} organisé avec succès.")
        
    except Exception as e:
        print(f"ERREUR lors de la réorganisation de {cluster_name} : {e}")
    
    os.chdir(BASE_DIR)
if __name__ == '__main__':
    main()