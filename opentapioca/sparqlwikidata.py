import requests

def sparql_wikidata(query_string, endpoint='https://query.wikidata.org/sparql'):
    results = requests.get(endpoint, {'query': query_string, 'format': 'json'}).json()
    return results['results']
