"""Requêtes réseau contrôlées; une indisponibilité ne doit pas bloquer la saisie manuelle."""
import requests
def get_json(url, params=None):
    response=requests.get(url,params=params,timeout=12,headers={'User-Agent':'HVACBuilding/0.3 (public building prediagnostic)','Accept':'application/json'})
    response.raise_for_status()
    return response.json()
