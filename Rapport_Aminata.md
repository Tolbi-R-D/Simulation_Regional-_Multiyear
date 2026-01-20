Rapport : Génération de données climatiques et simulations régionales AquaCrop

Au cours de ces dernières semaines, j’ai travaillé sur la génération de données synthétiques, notamment la simulation des données climatiques et régionales pour le modèle AquaCrop.
Ce travail se déroule en plusieurs étapes :

1. Clustering
Dans ce cas pratique, j’ai utilisé QGIS comme outil de traitement spatial. Le Sénégal a été défini comme zone d’étude, puis sa carte a été découpée en plusieurs clusters de 31 × 31 m, regroupés dans un seul fichier GeoJSON, sans modification de la géométrie initiale.

2. Génération de plusieurs fichiers GeoJSON
Dans cette étape, j’ai développé un script Python permettant d’extraire chaque cluster et de lui attribuer un fichier GeoJSON unique. Le script prend en entrée un seul fichier GeoJSON contenant l’ensemble des clusters et génère automatiquement des fichiers GeoJSON distincts pour chaque cluster.

3. Simulation des données climatiques (forecast)
J’ai cloné un script qui automatise la chaîne de traitement des données climatiques. Celui-ci commence par analyser la géométrie des fichiers GeoJSON afin de définir les zones de culture (20 clusters sélectionnés aléatoirement) au Sénégal. Il calcule ensuite leurs centres et leurs limites géographiques, avec une marge de sécurité afin de garantir une couverture météorologique complète.
Le script interroge ensuite les serveurs de Copernicus (ECMWF) pour fusionner deux horizons temporels essentiels :
Les données historiques ERA5, qui décrivent les conditions réelles (précipitations, vent, température) depuis le début de la saison agricole ;
Les prévisions saisonnières SEAS5, couvrant les mois à venir.
Cette fusion hybride permet d’assurer une continuité temporelle des données, indispensable pour simuler l’intégralité de la campagne agricole, du semis jusqu’à la récolte prévue.
Les données climatiques brutes (en Kelvin, en Joules, etc.) sont ensuite converties en indicateurs agronomiques :
PLU (Précipitations) : cumul quotidien en millimètres ;
Tnx (Températures) : détermination des températures minimales et maximales journalières ;
ETo (Évapotranspiration de référence) : étape la plus complexe, basée sur l’algorithme de Penman-Monteith, qui estime la quantité d’eau évapotranspirée par le sol et les plantes en fonction de l’ensoleillement, du vent et de l’humidité.
Enfin, le code traduit ces résultats dans le format spécifique requis par le logiciel AquaCrop de la FAO.

4. Prédire la texture de sol de aquacrop
prédire la texture de sol d’un seul point (code javascript et python) : 
La texture du sol est obtenue en calculant les proportions moyennes de sable, de limon et d’argile pour chaque polygone. Ces fractions granulométriques sont ensuite normalisées et utilisées pour attribuer une classe texturale selon la classification USDA, telle qu’employée dans le modèle AquaCrop.
Prédire la texture de sol de plusieurs points(python)

5. Génération des fichiers sol (.SOL) pour AquaCrop : 
Pour préparer les simulations AquaCrop, un script Python a été conçu pour transformer un fichier unique de textures de sol en plusieurs fichiers sol (.SOL) distincts, chaque fichier correspondant à un cluster spatial.
Le fichier d’entrée est un GeoJSON contenant, pour chaque cluster, un identifiant unique (id) et une classe de texture du sol (aquacrop_texture). Le script parcourt les polygones et génère automatiquement un fichier .SOL dont le nom reprend l’identifiant du cluster, assurant ainsi une correspondance avec les données climatiques utilisées pour chaque cluster.

6. Automatisation des simulations régionales AquaCrop
Cette partie vise à automatiser l’exécution massive du modèle de culture AquaCrop (versions 7.1/7.2) sur l’ensemble du territoire sénégalais. Le système permet de simuler les rendements agricoles en combinant systématiquement trois dimensions :
Sites climatiques : différentes zones géographiques ;
Clusters : sous-unités climatiques spécifiques à chaque zone ;
Types de sols : différents profils pédologiques (sol1, sol2, etc.).
Les données climatiques générées à l’étape 3 (PLU, ETo, Tnx) sont utilisées comme données d’entrée, et deux scripts principaux sont exécutés.
Script 1 : AC_exec_Aminata.py
Ce script agit comme un chef d’orchestre chargé de la gestion globale des simulations :
Exploration dynamique : analyse automatique des répertoires d’entrée pour détecter les sites, clusters et types de sols disponibles ;
Génération des combinaisons : création de la matrice de simulation (Site × Cluster × Sol) ;
Gestion de l’environnement :
Création d’un répertoire temporaire isolé pour chaque simulation ;
Déploiement de l’exécutable aquacrop.exe et de l’arborescence requise (SIMUL/, OUTP/, LIST/) ;
Exécution : lancement des simulations via subprocess et nettoyage automatique des fichiers temporaires après l’archivage des résultats.
Script 2 : AC_PRM_Aminata.py
Le script AC_PRM_Aminata.py constitue le moteur de configuration et de lancement des simulations AquaCrop. Il permet de générer automatiquement les fichiers de projet .PRM et de lancer le modèle pour chaque cluster et chaque année de simulation.
Le script parcourt les différents sites climatiques et clusters présents dans les dossiers de données climatiques et sélectionne le fichier sol correspondant à chaque cluster. Pour chaque cluster, il crée un dossier de sortie structuré, dans lequel sont copiés l’exécutable AquaCrop ainsi que les fichiers et répertoires techniques nécessaires au fonctionnement du modèle (SIMUL/, OUTP/ et LIST/).

La génération des fichiers projet .PRM est réalisée automatiquement via la fonction run_ac_pro_yrs, en combinant de manière cohérente :
les fichiers climatiques spécifiques à chaque cluster (.CLI, .Tnx, .ETo, .PLU) ;
le fichier de culture standard (Mastrop143.CRO) ;
le fichier d’irrigation (Inet_50RAW.IRR) et le fichier de gestion du champ (SFR30.MAN) ;
le fichier sol correspondant au cluster, généré précédemment (.SOL).
Chaque projet inclut également :
les dates de début et de fin de simulation ;
les paramètres liés aux années simulées et aux cycles culturaux.

Le script assure la gestion chronologique des simulations en calculant les numéros de jours selon le format spécifique d’AquaCrop (référence à partir de l’année 1901) pour la période 2011–2016. Il configure également l’option KeepSWC, permettant de conserver l’état hydrique du sol d’une année sur l’autre et d’assurer la continuité des simulations pluriannuelles.

Une fois le fichier .PRM généré, AquaCrop est exécuté automatiquement via le module subprocess. À l’issue de l’exécution, le script réorganise les fichiers de sortie afin de faciliter leur exploitation, en supprimant les fichiers système inutiles et en conservant uniquement le fichier .PRM et les résultats détaillés.

Les résultats sont produits de manière structurée dans le répertoire OUTPUT, chaque simulation disposant de son propre dossier nommé selon la combinaison unique Site_Cluster_Sol. Le script extrait et archive en priorité le fichier .PRM, qui récapitule l’ensemble des conditions de simulation, ainsi que les résultats stockés dans le sous-dossier OUTP.

Cette automatisation permet de simuler efficacement plusieurs années et clusters, tout en garantissant une correspondance rigoureuse entre les données climatiques, les profils de sols et les paramètres culturaux utilisés.

Dans cette partie, j’ai rencontré plusieurs bugs : 
Le principal problème était le manque de généralisation sur plusieurs années : l’automatisation ne générait que la première année. Pour résoudre ce problème, j’ai vérifié les données d’entrée, aussi bien celles des sols que celles climatiques. J’ai même utilisé MERRA2, un jeu de données climatique mondial produit par la NASA (Goddard Space Flight Center), avec une résolution spatiale d’environ 0,5° × 0,625° (~50 km × 70 km), pour générer d’autres données climatiques, mais cela n’a pas résolu le problème. Cela a permis de confirmer que l’erreur ne venait pas des données d’entrée.
Ensuite, avec Docko, nous avons comparé les fichiers de sortie que j'avais générés avec ceux de référence. C'est à ce moment-là que nous avons constaté des différences au niveau des fichiers .PRM, ce qui a permis d'identifier que l'erreur se situait dans le code. Après cette analyse, nous avons modifié le code qui génère maintenant toutes les années sauf la dernière. Nous travaillons actuellement sur la simulation de la dernière année.

 




