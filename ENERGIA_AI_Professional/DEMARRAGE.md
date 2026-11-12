# ENERGIA AI — Professional Web Edition

Interface FastAPI + HTML/CSS/JavaScript, ajoutée à la V5 sans remplacer `engine.py`, `app.py` ou les modules métier.

## Windows PowerShell

Dans le dossier extrait :

```powershell
py -m pip install -r requirements-web.txt
py -m uvicorn web_api:app --host 127.0.0.1 --port 8000
```

Ouvrir http://127.0.0.1:8000. Ou double-cliquer sur `START_WINDOWS.bat`.

La V5 Streamlit reste accessible via `py -m streamlit run app.py`.

## Fonctionnalités

- Vue d'ensemble responsive et KPI complets
- Formulaire bâtiment et consommations annuelles
- Diagnostic et recommandations du moteur V5
- Conseiller IA local V5
- Export PDF avec le générateur V5

## Limites

Le graphique utilise Chart.js via CDN (nécessite internet pour ce graphique). Les calculs et les réponses locales fonctionnent sans clé API. L'interface ne sauvegarde pas les diagnostics après actualisation ; aucune base de données n'a été ajoutée. Les services d'identification publique et de préremplissage de la V5 Streamlit n'ont pas encore été raccordés à cette nouvelle interface. Cette édition doit être testée sur votre ordinateur avant déploiement. Ne pas exposer le serveur à Internet sans authentification et mesures de sécurité.
