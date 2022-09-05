#!/bin/sh
curl "https://www.wikidata.org/w/api.php?action=wbgetentities&ids=$1&format=json" | jq .entities.$1 > $1.json
