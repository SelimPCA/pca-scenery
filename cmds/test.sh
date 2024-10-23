#!/bin/bash
set -e

# NOTE: to install all versions execute the following
# for version in 3.11.8 3.12.3; do
#     pyenv install $version
# done
# TODO: add django versions in the matrix (see also github actions)

# Array of Python versions to test
PYTHON_VERSIONS=("3.11.8" "3.12.3") # 

for version in "${PYTHON_VERSIONS[@]}"; do
    echo "Testing with Python $version"
    
    # Clean up previous environment and build
    rm -rf "./env_test_$version"
    rm -rf ./build
    
    # Create and activate new environment
    ~/.pyenv/versions/$version/bin/python -m venv "env_test_$version"
    source "env_test_$version/bin/activate"
    
    # Install and test
    pip install --upgrade pip
    pip install .
    python -m rehearsal
    
    # Cleanup
    deactivate
    rm -rf "./env_test_$version"
    rm -rf ./build
    
    echo "Completed testing with Python $version"
    echo "----------------------------------------"
done

