set -e

# if venv is not active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    source env/bin/activate
fi

python3 -m pip install --upgrade build
python3 -m build