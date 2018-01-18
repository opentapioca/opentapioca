#!/bin/bash
set -e

solr create -c $1
curl -X POST -H 'Content-type:application/json'  http://localhost:8983/solr/$1/schema -d '{
  "add-field-type":{
    "name":"tag",
    "class":"solr.TextField",
    "postingsFormat":"Memory",
    "omitNorms":true,
    "multiValued":true,
    "indexAnalyzer":{
      "tokenizer":{ 
         "class":"solr.StandardTokenizerFactory" },
      "filters":[
        {"class":"solr.EnglishPossessiveFilterFactory"},
        {"class":"solr.ASCIIFoldingFilterFactory"},
        {"class":"solr.LowerCaseFilterFactory"},
        {"class":"org.opensextant.solrtexttagger.ConcatenateFilterFactory"}
      ]},
    "queryAnalyzer":{
      "tokenizer":{ 
         "class":"solr.StandardTokenizerFactory" },
      "filters":[
        {"class":"solr.EnglishPossessiveFilterFactory"},
        {"class":"solr.ASCIIFoldingFilterFactory"},
        {"class":"solr.LowerCaseFilterFactory"}
      ]}
    },

  "add-field":{ "name":"label", "type":"text_general"},

  "add-field":{ "name":"aliases", "type":"text_general", "multiValued":true },

  "add-field":{ "name":"desc", "type":"text_general", "indexed":false, "multiValued":false },

  "add-field":{ "name":"type", "type":"int", "indexed":false, "multiValued":true },

  "add-field":{ "name":"grid", "type":"text_general", "indexed":false, "multiValued":true },

  "add-field":{ "name":"edges", "type":"int", "indexed":false, "multiValued":true },

  "add-field":{ "name":"nb_statements", "type":"int", "indexed":false, "multiValued":false },

  "add-field":{ "name":"nb_sitelinks", "type":"int", "indexed":false, "multiValued":false },
  
  "add-field":{ "name":"name_tag", "type":"tag", "stored":false, "multiValued":true },
  
  "add-copy-field":{ "source":"label", "dest":[ "name_tag" ]},
  "add-copy-field":{ "source":"aliases", "dest":[ "name_tag" ]}
}'
curl -X POST -H 'Content-type:application/json' http://localhost:8983/solr/$1/config -d '{
  "add-requesthandler" : {
    "name": "/tag",
    "class":"org.opensextant.solrtexttagger.TaggerRequestHandler",
    "defaults":{ "field":"name_tag" }
  }
}'

