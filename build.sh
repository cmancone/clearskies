#!/usr/bin/env bash
poetry build
poetry publish --username __token__ --password $(akeyless get-secret-value -n /pypi)
