.DEFAULT_GOAL := help
help:
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

build: ## builds docker images
	docker-compose -f local.yml build

up: ## launches docker images
	docker-compose -f local.yml up --build --detach

logs: ## attaches to docker logs
	docker-compose -f local.yml logs -f --tail="100"

test: ## launches tests inside image
	docker-compose -f local.yml run tapioca python -m pytest tests

stop: ## stop docker images
	docker-compose -f local.yml stop

drop-solr: stop ## drop the local solr content
	docker-compose -f local.yml down
	docker volume rm  opentapioca_solr_data_local
