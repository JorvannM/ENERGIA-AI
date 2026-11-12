"""Correspondances prudentes; un DPE de logement n'est pas une donnée d'immeuble."""
import re, unicodedata
def norm(x):
    s=unicodedata.normalize('NFKD',str(x or '')).encode('ascii','ignore').decode().lower()
    return ' '.join(re.findall(r'[a-z0-9]+',s))
def first(row,*keys):
    for k in keys:
        v=row.get(k)
        if v not in (None,''):return v
    return None
def candidate_from_dpe(row,kind,address):
    dpe_address=first(row,'Adresse_brute','adresse_brute','Adresse_(BAN)','adresse_ban','adresse','Adresse')
    if not dpe_address:
        parts=[first(row,'Numero_voie','numero_voie'),first(row,'Type_voie','type_voie'),first(row,'Nom_rue','nom_rue'),first(row,'Code_postal_(BAN)','code_postal_ban'),first(row,'Nom__commune_(BAN)','nom_commune_ban')]
        dpe_address=' '.join(str(x) for x in parts if x is not None)
    query=norm(address); actual=norm(dpe_address)
    # Pas de validation automatique : même rue ne suffit pas.
    matching=bool(query and actual and (query==actual or query in actual or actual in query))
    surface=first(row,'Surface_habitable_logement','Surface_habitable_immeuble','Surface_utile','surface_utile','Surface_thermique_lot','surface_habitable_logement')
    try: surface=float(str(surface).replace(',','.')) if surface is not None else None
    except (ValueError,TypeError): surface=None
    if surface is not None and surface<=0:surface=None
    return {'id':str(first(row,'N°DPE','N°_DPE','numero_dpe','Numero_DPE','_id') or ''),'kind':kind,'address':dpe_address or 'Adresse non précisée','address_match':matching,'surface_m2':surface,'surface_type':'surface issue du DPE (périmètre à confirmer)' if surface else None,'construction_year':first(row,'Année_construction','annee_construction'),'heating_type':first(row,'Type_énergie_n°1','Type_énergie_principale_chauffage','type_energie_principale_chauffage'),'energy_class':first(row,'Etiquette_DPE','etiquette_dpe'),'ghg_class':first(row,'Etiquette_GES','etiquette_ges'),'raw':row,'source':'ADEME DPE '+kind,'warning':'DPE du logement ou de la partie diagnostiquée, pas nécessairement de l’immeuble entier.'}
