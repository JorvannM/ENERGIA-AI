from unittest.mock import patch
from building_enrichment import locate,enrich
from services.building_matcher import candidate_from_dpe
from services.prefill import approved_prefill
def test_pipeline():
    loc={'address':'10 rue de la Paix 75002 Paris','ban_id':'test','lat':48.0,'lon':2.0}
    with patch('building_enrichment.search_dpe',side_effect=[[{'Surface_habitable_logement':68,'Etiquette_DPE':'D','Adresse_brute':loc['address']}],[]]), patch('building_enrichment.search_bdnb',return_value=([],None)):
        result=enrich(loc)
    assert len(result['dpe'])==1
    assert result['dpe'][0]['surface_m2']==68
    assert approved_prefill(result['dpe'][0])['surface_m2']==68
    assert candidate_from_dpe({'Surface_habitable_logement':0},'logement_existant','x')['surface_m2'] is None
if __name__=='__main__':
    test_pipeline();print('Tests enrichissement : OK')
