import geopandas as gpd
import os
import re

def clean_name(text):
    """Nettoie le texte pour éviter les erreurs de nom de fichier."""
    return re.sub(r'[^\w\s-]', '', str(text)).strip().replace(' ', '_')

def create_formatted_sol_v6(input_path, output_path):
    # 1. Chargement des données
    try:
        gdf = gpd.read_file(input_path)
        print(f"--- Fichier chargé : {len(gdf)} polygones trouvés ---")
    except Exception as e:
        print(f"Erreur de lecture : {e}")
        return

    os.makedirs(output_path, exist_ok=True)

    # Colonnes basées sur votre fichier soil_aquacrop_20_clusters.geojson
    col_id = 'id'
    col_texture = 'aquacrop_texture'

    print(f"Génération des fichiers .SOL (Format strict)...")

    for index, row in gdf.iterrows():
        val_id = row[col_id]
        val_texture = row[col_texture]
        
        # Nom du fichier identique à l'appel dans le .PRM
        filename = f"cluster_{val_id}.SOL"
        full_path = os.path.join(output_path, filename)

        # 2. Construction avec ALIGNEMENT STRICT (Important pour AquaCrop 7.1)
        # On utilise deux horizons comme dans votre fichier de référence
        # Utilisez cet alignement strict dans votre script Python
        sol_content = (
            f"{val_texture} - Polygon ID {val_id}\n"
            f"   6.0       : AquaCrop Version (march 2017)\n"
            f"  46         : CN (Curve Number)\n"
            f"   4         : Readily evaporable water from top layer (mm)\n"
            f"   2         : Number of soil horizons\n"
            f"  -9         : Depth (m) of restrictive soil layer inhibiting root zone expansion\n"
            f"  Thickness  Sat    FC    WP     Ksat   Penetrability  Gravel  CRa       CRb           description\n"
            f"  ---(m)---  -----(vol %)-----  (mm/day)      (%)        (%)    -----------------------------------------\n"
            f"    0.30     42.3  11.7   2.3    1900.5         100         3    -0.330205   0.330443     {val_texture}\n"
            f"    1.00     42.4  11.7   2.5     766.0         100         0    -0.318860   0.110895     {val_texture}"
        )

        # 3. Écriture avec sauts de ligne Windows (\r\n) pour le moteur Fortran
        with open(full_path, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(sol_content)

    print(f"Terminé : {len(gdf)} fichiers .SOL générés dans {output_path}")

# --- CONFIGURATION ---
INPUT_FILE = r"C:\Users\admin\Desktop\Tolbi 2025\RegionalAC_Py\PreprocessingSol\soil_aquacrop.geojson"
# On envoie les fichiers directement là où AquaCrop les cherche (DirSoil)
OUTPUT_DIR = r"C:\Users\admin\Desktop\Tolbi 2025\RegionalAC_Py\PreprocessingSol\soil_20_clusters"

create_formatted_sol_v6(INPUT_FILE, OUTPUT_DIR)