# Changelog

All notable changes to OpenTapioca will be documented in this file.

## [Unreleased]

### TODO

- Multilingual Support
- Version control for Solr9 and above (e.g., possibly update configsets)
- Specific versions in Requirements.txt

## [0.1.3] - 2025-12-22

### Added

- Downloadable artifacts (i.e., BoW, PgRank, classifier/s)
	- Bag of Words LM:
	- Page Rank:
	- SVM Classifier:
- This CHANGELOG file to provide model artifacts trained on Wikidata dump (Pages: ≈119,927,045 pages) from 2025-12-10
- Fix to Issue #59
- Notes: 6g of heap memory was successful for indexing (4g resulted in no response from server)

## [0.1.2] - 2022-11-10

## [0.1.1] - 2021-01-04

## [0.1.0] - 2019-04-25

### Added

- live updates via the Wikimedia EventStream;
- NIF endpoint;
- supports custom Solr analzyer;
