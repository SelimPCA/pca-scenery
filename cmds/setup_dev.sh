set -e

rm -rf ./env

# install python
~/.pyenv/versions/3.12.3/bin/python -m venv env

# active environment
source env/bin/activate

# install dependencies
pip install --upgrade pip
pip install -e .


