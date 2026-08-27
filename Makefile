UV := uv

.PHONY: sync lock run test validate build docker-build docker-run

sync:
	$(UV) sync --locked

lock:
	$(UV) lock

run:
	$(UV) run kobo-book-downloader $(ARGS)

test:
	$(UV) run pytest

validate:
	$(UV) lock --check
	$(UV) run pytest
	$(UV) build

build:
	$(UV) build

docker-build:
	docker build -t kobo-book-downloader .

docker-run:
	docker compose run --rm kobo $(ARGS)
