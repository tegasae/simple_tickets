#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: bash reproduce.sh current|refresh|patched|historical-current|historical-patched|smoke-current|smoke-patched [pytest options]" >&2
    exit 2
fi

mode=$1
shift
tests_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
review_dir=$(dirname "$tests_dir")
repo=$(git -C "$review_dir" rev-parse --show-toplevel)
snapshot=869cd424b1b9f13babd720884a3cbb7e0f6a10bb
python_cmd=${ACCEPTANCE_PYTHON:-python3}
temp=$(mktemp -d)
trap 'rm -rf "$temp"' EXIT
source_dir="$temp/source"
mkdir "$source_dir"
git -C "$repo" archive "$snapshot" src utils db/schema.sql main.py models.py config.py \
    pytest.ini requirements.txt requirements-test.txt | tar -xf - -C "$source_dir"
cp "$source_dir/db/schema.sql" "$temp/legacy-schema.sql"
export ACCEPTANCE_LEGACY_SCHEMA="$temp/legacy-schema.sql"
export PYTHONPATH="$source_dir"
export PYTHONDONTWRITEBYTECODE=1
cp -r "$tests_dir" "$source_dir/acceptance_tests"
cd "$source_dir"

apply_patch() {
    local patch_file=$1
    git apply --check --whitespace=error-all "$patch_file"
    git apply --whitespace=error-all "$patch_file"
}
if [[ "$mode" == refresh || "$mode" == patched || "$mode" == historical-patched || "$mode" == smoke-patched ]]; then
    apply_patch "$review_dir/patches/05-shared-refresh-and-versions.patch"
fi
if [[ "$mode" == patched || "$mode" == historical-patched || "$mode" == smoke-patched ]]; then
    for patch_file in "$review_dir"/patches/0[6-9]-*.patch "$review_dir"/patches/10-*.patch; do
        apply_patch "$patch_file"
    done
fi
suite=acceptance_tests
case "$mode" in
    current|refresh|patched) ;;
    smoke-current|smoke-patched)
        old_check=reviews/python-backend/recheck-5288dea/tests/check_backend.py
        git -C "$repo" show "$snapshot:$old_check" > "$temp/check_backend.py"
        "$python_cmd" "$temp/check_backend.py"
        if [[ "$mode" == smoke-patched ]]; then
            "$python_cmd" -m ast scripts/migrate_backend_storage.py > /dev/null
        fi
        exit 0
        ;;
    historical-current|historical-patched)
        old=reviews/python-backend/recheck-bbf7a39/tests
        git -C "$repo" archive "$snapshot" "$old" | tar -xf - -C "$source_dir"
        mv "$old" last_review_tests
        suite=last_review_tests
        ;;
    *) echo "Unknown run mode" >&2; exit 2 ;;
esac
"$python_cmd" -m pytest -c pytest.ini -o addopts='' -p no:cacheprovider -q --tb=short "$suite" "$@"
