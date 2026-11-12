# HVAC Building — Identification automatique v0.3
Lancer `python -m pip install -r requirements.txt` puis `python -m streamlit run app.py`.

Dans **Bâtiment**, saisir une adresse, sélectionner l'adresse exacte, lancer la recherche,
vérifier un DPE candidat et cocher la confirmation avant préremplissage.
Dans **Audit énergétique**, vérifier la surface et saisir les consommations réelles.

Sources : Géoplateforme (`data.geopf.fr`), ADEME DPE logements existants (`dpe03existant`),
ADEME tertiaire (`dpe01tertiaire`). Les résultats peuvent être absents ou imprécis.
Le connecteur BDNB est un point d'intégration **non configuré par défaut** :
définir `HVAC_BDNB_SEARCH_URL` uniquement après validation du chemin et des filtres
avec la documentation Swagger de https://api.bdnb.io/v1/bdnb.
Aucun résultat BDNB n'est inventé. Les DPE sont des candidats, non des identifications certifiées.

Tests hors ligne : `python tests_smoke.py` et `python tests_enrichment.py`.
Les API externes n'ont pas été testées en direct dans cet environnement.
