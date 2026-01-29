import geopandas as gpd
import os
import re

def safe_filename(text):
    """
    Crée un nom de fichier sûr à partir d'une chaîne de texte.
    Remplace les caractères non alphabétiques, non numériques et non tirets
    par des tirets bas.
    """
    text = str(text).strip()
    # Conserve les mots, les nombres, les espaces et les tirets.
    text = re.sub(r'[^\w\s-]', '', text)
    # Remplace les espaces et les tirets multiples par un seul tiret bas.
    text = re.sub(r'[-\s]+', '_', text)
    return text.lower()


def split_geojson_by_cluster(input_file_path, cluster_column_name, output_directory):
    """
    Lit un fichier GeoJSON, le découpe en fichiers GeoJSON séparés
    basés sur les valeurs uniques d'une colonne de cluster spécifiée.
    """
    
    print(f"--- Début du traitement pour {input_file_path} ---")

    # 1. Lecture du fichier GeoJSON
    try:
        # Tente de lire le fichier en utilisant le chemin d'entrée
        gdf = gpd.read_file(input_file_path) 
    except Exception as e:
        print(f"Erreur: Impossible de lire le fichier GeoJSON. Assurez-vous que le chemin est correct. Cause : {e}")
        return

    # 2. Vérification de la colonne de cluster
    if cluster_column_name not in gdf.columns:
        print(f"Erreur: La colonne '{cluster_column_name}' est introuvable dans le fichier.")
        print("Veuillez vérifier le nom de la colonne. Colonnes disponibles:", gdf.columns.tolist())
        return

    # 3. Création du dossier de sortie
    os.makedirs(output_directory, exist_ok=True)
    print(f"Dossier de sortie créé ou existant: '{output_directory}'")

    # 4. Identification et nettoyage des clusters
    # Supprime les lignes où l'ID de cluster est manquant (NaN)
    gdf_cleaned = gdf.dropna(subset=[cluster_column_name])
    unique_clusters = gdf_cleaned[cluster_column_name].unique()
    print(f"Nombre de clusters uniques trouvés à découper: {len(unique_clusters)}")

    # 5. Boucle et Sauvegarde de chaque cluster
    for cluster_id in unique_clusters:
        # Filtrer les données pour le cluster actuel
        cluster_data = gdf_cleaned[gdf_cleaned[cluster_column_name] == cluster_id]
        
        # Créer un nom de fichier sûr
        safe_name = safe_filename(cluster_id)
        
        # Définir le chemin de sortie
        output_filename = os.path.join(output_directory, f"cluster_{safe_name}.geojson")
        
        # Sauvegarder dans un nouveau fichier GeoJSON
        try:
            cluster_data.to_file(output_filename, driver='GeoJSON')
            print(f"  - Cluster '{cluster_id}' ({len(cluster_data)} entités) sauvegardé.")
        except Exception as e:
            print(f"  - Erreur lors de la sauvegarde du cluster '{cluster_id}' : {e}")

    print("--- Opération de découpage terminée avec succès! ---")


# =========================================================================
## Configuration et Exécution
# =========================================================================

# 1. CHEMIN COMPLET DU FICHIER EN ENTRÉE (GeoJSON original)
# Utilisation de 'r""' (raw string) pour gérer les barres obliques Windows
INPUT_FILE = r"C:\Users\admin\Desktop\Tolbi 2025\Cluster_Sénégal_31X31\20_clusters_senegal.geojson"

# 2. NOM DE LA COLONNE CONTENANT L'IDENTIFIANT DU CLUSTER
# Le nom 'id' est utilisé ici comme demandé, mais vérifiez toujours qu'il est correct.
CLUSTER_COLUMN_NAME = 'id' 

# 3. CHEMIN COMPLET DU DOSSIER DE SORTIE
OUTPUT_DIR = r"C:\Users\admin\Desktop\Tolbi 2025\Cluster_Sénégal_31X31\output_20_clusters_senegal"
# =========================================================================

# Exécution de la fonction
split_geojson_by_cluster(INPUT_FILE, CLUSTER_COLUMN_NAME, OUTPUT_DIR)