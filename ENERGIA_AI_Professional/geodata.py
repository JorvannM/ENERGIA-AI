
import requests


def geocode_address(address):
    """
    Recherche une adresse avec le service public de géocodage IGN.
    """
    url = "https://data.geopf.fr/geocodage/search"

    try:
        response = requests.get(
            url,
            params={
                "q": address,
                "limit": 1
            },
            timeout=15
        )

        response.raise_for_status()

        data = response.json()
        features = data.get("features", [])

        if not features:
            return None

        feature = features[0]
        properties = feature.get("properties", {})
        coordinates = feature.get("geometry", {}).get("coordinates", [])

        if len(coordinates) < 2:
            return None

        return {
            "address": properties.get("label", address),
            "lon": float(coordinates[0]),
            "lat": float(coordinates[1]),
            "source": "Géoplateforme IGN"
        }

    except Exception as error:
        print("Erreur géocodage :", error)
        return None


def search_tertiary_dpe(address):
    """
    Fonction temporaire : recherche DPE désactivée
    tant que l'API ADEME n'est pas validée.
    """
    return []
