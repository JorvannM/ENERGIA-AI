# HVAC Building — version améliorée (moteur modulaire)

## Architecture
- `engine.py` : orchestration et compatibilité avec l'ancienne interface Streamlit.
- `data_model.py` : modèle de données bâtiment.
- `validation.py` : contrôles de saisie et cohérence.
- `heating.py`, `cooling.py`, `ventilation.py`, `lighting.py`, `hot_water.py` : diagnostics par usage.
- `exploitation.py` : horaires, consignes, sous-comptage et pilotage.
- `economics.py` : économies et indicateurs économiques.
- `carbon.py` : calcul carbone avec facteurs externes versionnés.
- `recommendations.py` : actions traçables, non chiffrées sans preuve suffisante.
- `data/diagnostics_rules.json` : seuils et règles de screening.
- `data/emission_factors.json` : facteurs d'émission provisoires et métadonnées.

## Installation Windows / PowerShell
Depuis le dossier du projet :
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Si l'environnement `.venv` existe déjà, ne le recrée pas.

## Vérification rapide
```powershell
.\.venv\Scripts\python.exe tests_smoke.py
```

## Principes et limites
Les sorties sont un **pré-diagnostic d'aide à la décision**, pas un DPE ni un audit réglementaire.
Les consommations doivent couvrir une période cohérente. Les économies ne sont pas additionnées entre postes car elles peuvent se recouvrir.
Les facteurs carbone sont provisoires : remplacer/valider les valeurs avec les facteurs officiels correspondant à l'année, au vecteur énergétique, au réseau et au périmètre étudiés.
Les modules techniques fournissent des contrôles et pistes d'investigation. Ils ne prétendent pas calculer une performance saisonnière, un dimensionnement ou une conformité sans mesures et données système.
