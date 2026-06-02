# AI Client Report Generator

set positional-arguments

default:
    @just --list

run *ARGS:
    #!/usr/bin/env bash
    set -euo pipefail
    filtered=()
    for arg in "$@"; do
        [[ "$arg" == "--" ]] && continue
        filtered+=("$arg")
    done
    exec uv run python main.py "${filtered[@]}"

text:
    uv run main.py -f samples/dialog_example.txt

image quality="medium":
    uv run main.py -t design -q {{quality}} -f samples/design_dialog_example.txt

api:
    uv run python api.py

lint:
    uv run ruff check

fix:
    uv run ruff check --fix

format:
    uv run ruff format
