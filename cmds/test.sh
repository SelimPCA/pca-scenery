set -e

# if venv is active
if [[ "$VIRTUAL_ENV" != "" ]]; then

    # deactivate
    source env/bin/activate
    deactivate
fi

# delete existing env and build
rm -rf ./env_test
rm -rf ./build

# install python
~/.pyenv/versions/3.12.3/bin/python -m venv env_test

# active environment
source env_test/bin/activate

# install dependencies


pip install --upgrade pip
pip install .

python -m rehearsal
