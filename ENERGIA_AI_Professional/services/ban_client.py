from services.http_client import get_json
def geocode(query):
    payload=get_json('https://data.geopf.fr/geocodage/search',{'q':query,'limit':5})
    out=[]
    for f in payload.get('features',[]):
        p=f.get('properties') or {}; c=(f.get('geometry') or {}).get('coordinates') or []
        if len(c)>=2:
            out.append({'address':p.get('label',query),'lat':float(c[1]),'lon':float(c[0]),'score':p.get('score'),'ban_id':p.get('id'),'postcode':p.get('postcode'),'city':p.get('city'),'housenumber':p.get('housenumber'),'street':p.get('street'),'source':'Géoplateforme'})
    return out
