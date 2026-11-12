"""API ADEME Data Fair: recherche indicative, jamais une preuve de correspondance bâtiment."""
from services.http_client import get_json
BASE='https://data.ademe.fr/data-fair/api/v1/datasets/'
DATASETS={'logement_existant':'dpe03existant','tertiaire':'dpe01tertiaire'}
def search_dpe(address, kind, limit=12):
    dataset=DATASETS[kind]
    data=get_json(BASE+dataset+'/lines',{'q':address,'size':min(limit,30)})
    return data.get('results',[]) if isinstance(data,dict) else []
