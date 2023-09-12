.PHONY: schemas tests style_checks pre_commit_checks

schemas:
	poetry run datamodel-codegen --input components/renku_data_services/crc_schemas/api.spec.yaml --input-file-type openapi --output-model-type pydantic_v2.BaseModel --output components/renku_data_services/crc_schemas/apispec.py --use-double-quotes --target-python-version 3.11 --collapse-root-models --field-constraints --strict-nullable --base-class renku_data_services.crc_schemas.base.BaseAPISpec
	poetry run datamodel-codegen --input components/renku_data_services/storage_schemas/api.spec.yaml --input-file-type openapi --output-model-type pydantic_v2.BaseModel --output components/renku_data_services/storage_schemas/apispec.py --use-double-quotes --target-python-version 3.11 --collapse-root-models --field-constraints --strict-nullable --base-class renku_data_services.storage_schemas.base.BaseAPISpec

style_checks:
	poetry check
	poetry run mypy
	poetry run flake8 -v
	poetry run bandit -c pyproject.toml -r .
	poetry run isort --diff --verbose .
	poetry run pydocstyle -v
	poetry poly check
	poetry poly libs

tests:
	@rm -f .tmp.pid coverage.lcov .coverage data_services.db
	poetry run pytest
	@echo "===========================================DATA API==========================================="
	DUMMY_STORES=true poetry run coverage run -a -m sanic --debug --single-process renku_data_services.data_api.main:create_app --factory & echo $$! > .tmp.pid
	@sleep 10
	-poetry run st run http://localhost:8000/api/data/spec.json --validate-schema True --checks all --hypothesis-max-examples 20 --data-generation-method all --show-errors-tracebacks --hypothesis-suppress-health-check data_too_large --max-response-time 100 -v --header "Authorization: bearer some-random-key-123456"
	cat .tmp.pid | xargs kill
	@rm -f .tmp.pid
	@echo "===========================================TEST DOWNGRADE==========================================="
	DUMMY_STORES=true poetry run coverage run -a -m alembic -c components/renku_data_services/migrations/alembic.ini --name=storage downgrade base
	DUMMY_STORES=true poetry run coverage run -a -m alembic -c components/renku_data_services/migrations/alembic.ini --name=resource_pools downgrade base
	@echo "===========================================FINAL COMBINED COVERAGE FOR ALL TESTS==========================================="
	poetry run coverage report --show-missing
	poetry run coverage lcov -o coverage.lcov

pre_commit_checks:
	poetry run pre-commit run --all-files