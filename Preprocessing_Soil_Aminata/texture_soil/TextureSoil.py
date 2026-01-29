# =======================
# CODE COMPLET GEE + SOILGRIDS + USDA + AQUACROP
# (GeoJSON local → Earth Engine)
# =======================

import ee
import geopandas as gpd
import json

# Authentification et initialisation
ee.Authenticate()
ee.Initialize(project="ee-syllamina")

# -----------------------
# 2. Charger le GeoJSON local
# -----------------------
geojson_path = r"C:\Users\admin\Desktop\Tolbi 2025\Cluster_Sénégal_31X31\output_clusters_senegal_4326\cluster_81.geojson"

gdf = gpd.read_file(geojson_path)
geojson_dict = json.loads(gdf.to_json())

poly_fc = ee.FeatureCollection(geojson_dict)
poly = poly_fc.geometry()

# -----------------------
# 3. SOILGRIDS – TEXTURE
# -----------------------
sand = ee.Image('projects/soilgrids-isric/sand_mean').select('sand_0-5cm_mean')
silt = ee.Image('projects/soilgrids-isric/silt_mean').select('silt_0-5cm_mean')
clay = ee.Image('projects/soilgrids-isric/clay_mean').select('clay_0-5cm_mean')
soc  = ee.Image('projects/soilgrids-isric/soc_mean').select('soc_0-5cm_mean')

# -----------------------
# 4. EXTRACTION ZONALE
# -----------------------
stats = ee.Image.cat([sand, silt, clay, soc]).reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=poly,
    scale=250,
    maxPixels=1e13
)

# Convertir en nombres
sandPct = ee.Number(stats.get('sand_0-5cm_mean'))
siltPct = ee.Number(stats.get('silt_0-5cm_mean'))
clayPct = ee.Number(stats.get('clay_0-5cm_mean'))
socPct  = ee.Number(stats.get('soc_0-5cm_mean'))

# -----------------------
# 4b. Normaliser en pourcentages si nécessaire
# -----------------------
total = sandPct.add(siltPct).add(clayPct)
# Eviter division par zéro
total = ee.Algorithms.If(total.eq(0), 1, total)

sandPct = sandPct.divide(total).multiply(100)
siltPct = siltPct.divide(total).multiply(100)
clayPct = clayPct.divide(total).multiply(100)


print({
    "sand": sandPct.getInfo(),
    "silt": siltPct.getInfo(),
    "clay": clayPct.getInfo(),
    "SOC": socPct.getInfo()
})

# =======================
# 4. CLASSE TEXTURALE USDA (CORRIGÉE)
# =======================
usda = ee.Algorithms.If(
    sandPct.gte(85).And(clayPct.lt(10)), 'Sand',
    ee.Algorithms.If(
        sandPct.gte(70).And(clayPct.lt(15)), 'Loamy Sand',
        ee.Algorithms.If(
            sandPct.gte(43).And(sandPct.lt(85)).And(clayPct.gte(7)).And(clayPct.lt(20)), 'Sandy Loam',
            ee.Algorithms.If(
                siltPct.gte(80).And(clayPct.lt(12)), 'Silt',
                ee.Algorithms.If(
                    siltPct.gte(50).And(clayPct.lt(27)), 'Silt Loam',
                    ee.Algorithms.If(
                        sandPct.gte(45).And(clayPct.gte(35)), 'Sandy Clay',
                        ee.Algorithms.If(
                            siltPct.gte(40).And(clayPct.gte(40)), 'Silty Clay',
                            ee.Algorithms.If(
                                clayPct.gte(40), 'Clay',
                                ee.Algorithms.If(
                                    sandPct.gte(45).And(clayPct.gte(20)).And(clayPct.lt(35)), 'Sandy Clay Loam',
                                    ee.Algorithms.If(
                                        siltPct.gte(40).And(clayPct.gte(27)).And(clayPct.lt(40)), 'Silty Clay Loam',
                                        ee.Algorithms.If(
                                            clayPct.gte(27).And(clayPct.lt(40)), 'Clay Loam',
                                            'Loam'
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )
)

print('Classe USDA:', usda.getInfo())

# =======================
# 5. CONVERSION USDA → AQUACROP (.SOL)
# =======================
aquacropSoil = ee.Algorithms.If(
    ee.String(usda).equals('Sand'), 'Sand',
    ee.Algorithms.If(
        ee.String(usda).equals('Loamy Sand'), 'LoamySand',
        ee.Algorithms.If(
            ee.String(usda).equals('Sandy Loam'), 'SandyLoam',
            ee.Algorithms.If(
                ee.String(usda).equals('Loam'), 'Loam',
                ee.Algorithms.If(
                    ee.String(usda).equals('Silt Loam'), 'SiltLoam',
                    ee.Algorithms.If(
                        ee.String(usda).equals('Silt'), 'Silt',
                        ee.Algorithms.If(
                            ee.String(usda).equals('Sandy Clay Loam'), 'SandyClayLoam',
                            ee.Algorithms.If(
                                ee.String(usda).equals('Clay Loam'), 'ClayLoam',
                                ee.Algorithms.If(
                                    ee.String(usda).equals('Silty Clay Loam'), 'SiltClayLoam',
                                    ee.Algorithms.If(
                                        ee.String(usda).equals('Sandy Clay'), 'SandyClay',
                                        ee.Algorithms.If(
                                            ee.String(usda).equals('Silty Clay'), 'SiltyClay',
                                            'Clay'
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )
)

print('Texture AquaCrop:', aquacropSoil.getInfo())
