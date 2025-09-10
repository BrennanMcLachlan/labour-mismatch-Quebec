# Projet sur l'effet de l'inadéquation de la demande et de l'offre de travail sur le recrutement et le chômage du Québec

Un flux de travail automatisé GitHub Actions qui surveille, télécharge et traite les données de l’Enquête sur la population active (EPA) et de l’Enquête sur les postes vacants et les salaires (EPVS) de Statistique Canada afin de créer un jeu de données combiné avec des indices de désajustement et des visualisations.

## Aperçu

Ce flux de travail vérifie automatiquement chaque semaine si des mises à jour des ensembles de données de Statistique Canada sont disponibles et les traite dans un jeu de données final combiné.  
Il calcule les indices de désajustement entre les postes vacants et les statistiques de la main-d’œuvre au Québec et en Ontario, et génère des graphiques de contribution par industrie pour le Québec.

## Fonctionnalités

- **Surveillance automatisée** : S’exécute chaque lundi à 7 h UTC
- **Intégration des données** : Combine les données de l’EPA et de l’EPVS en un jeu de données unifié
- **Analyse du désajustement** : Calcule des indices entre l’offre et la demande de travail, et génère des graphiques de contribution par industrie
- **Contrôle de version** : Sauvegarde automatiquement les données traitées et les métadonnées dans le dépôt
- **Déclenchement manuel** : Possibilité de lancer le flux manuellement avec option de téléchargement forcé

## Sources de données

Le flux de travail traite deux ensembles de données principaux de Statistique Canada :
1. **Enquête sur la population active (EPA)** – Statistiques sur l’emploi et le marché du travail
2. **Enquête sur les postes vacants et les salaires (EPVS)** – Données sur les postes vacants par industrie

## Étapes du flux de travail

### 1. Configuration de l’environnement
- Configure Python 3.11
- Installe les dépendances requises

### 2. Vérification des mises à jour
- Exécute `check_updates.py` pour déterminer si de nouvelles données sont disponibles
- Compare les périodes de référence en ligne avec celles stockées localement
- Définit des indicateurs en fonction de la disponibilité des mises à jour

### 3. Traitement des données (si mises à jour disponibles)
- Télécharge les données brutes dans un répertoire temporaire
- Traite les données EPA et EPVS via `process_data.py`
- Fait le sous-échantillonnage et la fusion via `subset_and_merge.py`
- Calcule les indices de désajustement et génère les graphiques via `calculate_mismatch_index.py`
- Supprime les fichiers temporaires

### 4. Génération des sorties
- Crée le jeu de données final (`processed_data/final_data.csv`)
- Génère les graphiques (sauvegardés dans le répertoire `figures/`)
- Met à jour les fichiers de métadonnées avec les périodes de référence et les journaux de téléchargement

### 5. Téléversement et enregistrement
- Téléverse les données traitées comme artefacts GitHub (conservation de 90 jours)
- Enregistre les jeux de données finaux et les métadonnées dans le dépôt

## Structure du dépôt

```
├── .github/workflows/
│ └── monitor-statscan-data.yml # Fichier du flux de travail
├── code/
│ ├── check_updates.py # Vérification des mises à jour
│ ├── process_data.py # Traitement des données brutes
│ ├── subset_and_merge.py # Sous-échantillonnage et fusion
│ └── calculate_mismatch_index.py # Analyse du désajustement et graphiques
├── data/
│ ├── last_reference_date_*.txt # Dates de référence enregistrées
│ └── download_log.txt # Journal de traitement
├── processed_data/
│ └── final_data.csv # Jeu de données final combiné
└── figures/
└── *.png # Graphiques et visualisations générés
```

## Exécution manuelle

Vous pouvez déclencher manuellement le flux de travail via l’interface GitHub Actions :

1. Aller à l’onglet **Actions** du dépôt
2. Sélectionner le flux **monitor-statscan-data**
3. Cliquer sur **Run workflow**
4. Optionnel : cocher **Force download** pour ignorer la vérification des dates

## Fichiers de sortie

### Jeux de données
- `processed_data/final_data.csv` : Données combinées EPA et EPVS avec variables calculées
- `data/last_reference_date_*.txt` : Fichiers de suivi des périodes de référence
- `data/download_log.txt` : Historique et journaux de traitement

### Visualisations
- `figures/*.png` : Graphiques de contribution sectorielle et indices de désajustement (en français et en anglais)

## Dépendances

Le flux de travail requiert les bibliothèques Python suivantes :
- `pandas` : Manipulation et analyse de données
- `requests` : Téléchargement de données via HTTP
- `beautifulsoup4` : Extraction et analyse HTML
- `numpy` : Calculs numériques
- `pyreadstat` : Lecture de formats statistiques
- `matplotlib` : Génération de graphiques

## Configuration

### Options de personnalisation
- Modifier la planification (cron) dans le fichier du flux pour changer l’heure d’exécution
- Ajuster la durée de conservation des artefacts (90 jours par défaut)
- Mettre à jour la version de Python ou les dépendances au besoin

## Suivi et dépannage

### État du flux
- Vérifiez l’onglet **Actions** pour l’historique et l’état des exécutions
- Consultez les journaux pour plus de détails sur le traitement

### Problèmes fréquents
- **Aucune mise à jour** : Le flux indique simplement qu’aucune nouvelle donnée n’est disponible
- **Erreurs de traitement** : Vérifier les journaux des scripts Python pour le détail
- **Conflits de commit** : Le flux gère la résolution via stash/unstash

## Mises à jour des données

Le flux suit la fraîcheur des données via les périodes de référence :
- Période de référence EPA
- Période de référence EPVS
- Horodatage du traitement combiné

Les données ne sont traitées que lorsqu’au moins un des deux ensembles est mis à jour depuis la dernière exécution.

## Licence

Ce flux de travail traite des données publiques qui relèvent de la Licence ouverte de Statistique Canada (voir https://www.statcan.gc.ca/fr/conditions-licence/licence)

