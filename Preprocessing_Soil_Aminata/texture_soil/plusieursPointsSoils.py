import ee
import geopandas as gpd
import json
import pandas as pd

# -----------------------
# 1. Initialisation GEE
# -----------------------
ee.Authenticate()
ee.Initialize(project="ee-syllamina")

# -----------------------
# 2. Charger les polygones
# -----------------------
geojson_path = r"C:\Users\admin\Desktop\Tolbi 2025\Cluster_Sénégal_31X31\20_clusters_senegal.geojson"
gdf = gpd.read_file(geojson_path)

if 'id' not in gdf.columns:
    gdf['id'] = range(len(gdf))

for col in gdf.select_dtypes(include=['datetime64[ns]']).columns:
    gdf[col] = gdf[col].astype(str)

cols_to_keep = ['id', 'geometry']
gdf_clean = gdf[cols_to_keep]

fc = ee.FeatureCollection(json.loads(gdf_clean.to_json()))

# -----------------------
# 3. Charger SoilGrids (0–5 cm)
# -----------------------
sand = ee.Image('projects/soilgrids-isric/sand_mean').select('sand_0-5cm_mean')
silt = ee.Image('projects/soilgrids-isric/silt_mean').select('silt_0-5cm_mean')
clay = ee.Image('projects/soilgrids-isric/clay_mean').select('clay_0-5cm_mean')
soc  = ee.Image('projects/soilgrids-isric/soc_mean').select('soc_0-5cm_mean')

# -----------------------
# 4. Fonction de calcul optimisée pour AquaCrop
# -----------------------
def compute_soil(feature):
    geom = feature.geometry()
    
    stats = ee.Image.cat([sand, silt, clay, soc]).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=250,
        maxPixels=1e13
    )
    
    # SoilGrids est en g/kg -> On divise par 10 pour avoir du %
    sandPct = ee.Number(stats.get('sand_0-5cm_mean', 0)).divide(10)
    siltPct = ee.Number(stats.get('silt_0-5cm_mean', 0)).divide(10)
    clayPct = ee.Number(stats.get('clay_0-5cm_mean', 0)).divide(10)
    socVal  = ee.Number(stats.get('soc_0-5cm_mean', 0)).divide(10) # SOC en g/kg -> %

    # Normalisation pour assurer 100%
    total = sandPct.add(siltPct).add(clayPct)
    total = ee.Algorithms.If(total.eq(0), 1, total)
    
    s = sandPct.divide(total).multiply(100)
    l = siltPct.divide(total).multiply(100) # l pour limon/silt
    c = clayPct.divide(total).multiply(100)

    # Logique de classification USDA compatible AquaCrop
    # L'ordre respecte les priorités du triangle textural
    aquacrop_texture = ee.Algorithms.If(c.gte(40).And(s.lt(45)).And(l.lt(40)), 'Clay',
        ee.Algorithms.If(c.gte(40).And(l.gte(40)), 'Silty clay',
        ee.Algorithms.If(c.gte(35).And(s.gt(45)), 'Sandy clay',
        ee.Algorithms.If(c.gte(27).And(c.lt(40)).And(s.gt(45)), 'Sandy clay loam',
        ee.Algorithms.If(c.gte(27).And(c.lt(40)).And(s.lte(20)), 'Silty clay loam',
        ee.Algorithms.If(c.gte(27).And(c.lt(40)), 'Clay loam',
        ee.Algorithms.If(l.gte(80).And(c.lt(12)), 'Silt',
        ee.Algorithms.If(l.gte(50).And(c.lt(27)), 'Silt loam',
        ee.Algorithms.If(c.gte(7).And(c.lt(27)).And(l.gte(28)).And(s.lte(52)), 'Loam',
        ee.Algorithms.If(s.gte(85).And(l.add(c.multiply(1.5)).lt(15)), 'Sand',
        ee.Algorithms.If(s.gte(70).And(l.add(c.multiply(1.5)).gte(15)), 'Loamy sand',
        'Sandy loam')))))))))))

    return feature.set({
        'id': feature.get('id'),
        'sand_pct': s,
        'silt_pct': l,
        'clay_pct': c,
        'soc_pct': socVal,
        'aquacrop_texture': aquacrop_texture
    })

# -----------------------
# 5. Exécution et récupération
# -----------------------
results_fc = fc.map(compute_soil)
features = results_fc.getInfo()['features']

# Construction du DataFrame
rows = [f['properties'] for f in features]
df_results = pd.DataFrame(rows)

# -----------------------
# 6. Jointure et Sauvegarde
# -----------------------
gdf_out = gdf_clean.merge(df_results, on='id')
output_path = r"C:\Users\admin\Desktop\soil_aquacrop.geojson"
gdf_out.to_file(output_path, driver='GeoJSON')

print(f"✅ Traitement terminé. Fichier sauvegardé : {output_path}")
print(df_results.head())