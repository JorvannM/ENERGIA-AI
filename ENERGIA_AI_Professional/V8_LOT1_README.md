# ENERGIA AI V8 — Lot 1 (prototype local)

Cette version conserve le moteur V5, la recherche DPE, le design, le PDF et ajoute « Mes bâtiments » avec sauvegarde SQLite locale. **Ne pas déployer sur Internet** : les endpoints V8 n’ont pas encore d’authentification ni d’isolation entre entreprises. PostgreSQL, comptes et permissions restent à réaliser dans le lot suivant.

## Démarrer

Depuis le dossier `ENERGIA_AI_Professional` :

```powershell
py -m pip install -r requirements-web.txt
py -m uvicorn web_api:app --host 127.0.0.1 --port 8000
```

Ouvrir http://127.0.0.1:8000 puis « Mes bâtiments ». Dans « Bâtiment », cliquer « Enregistrer dans Mes bâtiments » pour sauvegarder la fiche. Charger ensuite ce bâtiment et lancer le diagnostic pour sauvegarder un audit. Le stockage est local dans `local_data/energia.sqlite3`, ignoré par Git.

## GitHub

Conserver `main` intacte ; publier cette version dans `feature/v8-foundations`. Vérifier `git status` avant tout commit.

## Limites

Les audits historiques sont consultables via l'API et leurs dates dans l'interface; la restauration visuelle d'un ancien audit et l'archivage des PDF ne sont pas encore intégrés. SQLite est destiné au prototype local, PostgreSQL sera nécessaire pour une exploitation multi-utilisateurs. Ne pas publier de données réelles sensibles.
