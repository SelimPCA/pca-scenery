set -e

python3 -m pip install --upgrade twine
python3 -m twine upload --repository testpypi dist/* --verbose