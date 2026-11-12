"""Client BDNB. Le chemin de requête peut évoluer selon la version de l'API."""
import os
from services.http_client import get_json
BASE='https://api.bdnb.io/v1/bdnb'
def search_bdnb(ban_id):
    # Chemin et filtre à confirmer avec le Swagger de l'instance BDNB.
    # Désactivé par défaut pour ne pas simuler une intégration opérationnelle.
    endpoint=os.getenv('HVAC_BDNB_SEARCH_URL','').strip()
    if not endpoint:
        return [], 'Connecteur BDNB à configurer (HVAC_BDNB_SEARCH_URL).'
    if not endpoint.startswith('https://api.bdnb.io/'):
        return [], 'URL BDNB refusée : domaine non autorisé.'
    try:
        payload=get_json(endpoint,{'cle_interop_adr':ban_id})
        if isinstance(payload,list):return payload[:20],None
        if isinstance(payload,dict):
            return (payload.get('results') or payload.get('features') or [])[:20],None
        return [],'Format BDNB non reconnu.'
    except Exception as e:
        return [],f'BDNB indisponible : {type(e).__name__}'
