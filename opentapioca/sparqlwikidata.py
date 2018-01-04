import requests

def sparql_wikidata(query_string):
    results = requests.get('https://query.wikidata.org/sparql', {'query': query_string, 'format': 'json'}).json()
    return results['results']
