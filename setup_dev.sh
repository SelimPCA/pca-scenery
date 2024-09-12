~/.pyenv/versions/3.12.3/bin/python -m venv env
source env/bin/activate
pip install -r requirements.txt
pip install -e .
deactivate