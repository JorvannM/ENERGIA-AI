# HVAC Building — v0.4 enrichissement et rapport PDF

## Installation (Windows / VS Code)

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

1. Dans **Bâtiment**, recherchez une adresse et sélectionnez un DPE correspondant au bien audité.
2. Confirmez le périmètre et cliquez sur **Préremplir**.
3. Dans **Audit énergétique**, contrôlez les caractéristiques préremplies et saisissez les consommations réelles (valeurs initiales à zéro).
4. Cliquez sur **Calculer les indicateurs**.
5. Dans **Rapports & méthode**, cliquez sur **Télécharger le rapport PDF**.

## Limites importantes

- Les champs DPE sont renseignés uniquement si le jeu de données fournit une valeur reconnue ; les données manquantes restent vides.
- Les champs DPE et BDNB ne prouvent pas la correspondance au bâtiment sans validation humaine.
- La BDNB demeure un connecteur **optionnel** via `HVAC_BDNB_SEARCH_URL` ; son endpoint doit être configuré et validé avant utilisation.
- Les données publiques et la connexion internet ne sont pas garanties ; les appels API externes n'ont pas été vérifiés en direct dans cet environnement.
- Ce rapport est un **pré-diagnostic**, pas un audit énergétique réglementaire.
