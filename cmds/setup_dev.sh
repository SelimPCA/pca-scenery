set -e

rm -rf ./env

# install python
~/.pyenv/versions/3.12.3/bin/python -m venv env

# active environment
source env/bin/activate

# install dependencies

# packaging
pip install --upgrade pip
python3 -m pip install --upgrade build
python3 -m pip install --upgrade twine

# doc building
python3 -m pip install --upgrade mkdocs
python3 -m pip install --upgrade mkdocs-material
python3 -m pip install --upgrade mkdocstrings[python]

# editable install of scenery
pip install -e .


