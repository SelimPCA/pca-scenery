set -e

# if venv is active
if [[ "$VIRTUAL_ENV" != "" ]]; then

    # deactivate
    source env/bin/activate
    deactivate
fi

rm -rf ./env

# install python
~/.pyenv/versions/3.12.3/bin/python -m venv env

# active environment
source env/bin/activate

# install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .


