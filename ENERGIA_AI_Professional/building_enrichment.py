"""Recherche de bâtiments: géocodage, DPE candidats, BDNB facultative."""
from services.ban_client import geocode
from services.ademe_client import search_dpe
from services.bdnb_client import search_bdnb
from services.building_matcher import candidate_from_dpe
def locate(address):
    return geocode(address)
def enrich(location):
    address=location['address']; result={'dpe':[],'bdnb':[],'warnings':[]}
    for kind in ('logement_existant','tertiaire'):
        try:
            records=search_dpe(address,kind)
            result['dpe'] += [candidate_from_dpe(r,kind,address) for r in records]
        except Exception as exc:
            result['warnings'].append(f'ADEME {kind} : {type(exc).__name__} (réseau/API indisponible ou recherche non prise en charge).')
    if location.get('ban_id'):
        result['bdnb'], warning=search_bdnb(location['ban_id'])
        if warning:result['warnings'].append(warning)
    else:result['warnings'].append('Identifiant BAN absent : recherche BDNB impossible.')
    return result
