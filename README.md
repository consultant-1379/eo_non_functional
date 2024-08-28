# Overview
This project contains automation scripts for eo non functional use cases.


## Requirements
* Python (version 3.11 or higher)
* File requirements.txt contains all required python packages.


## Project setup
1. Install python3-venv package.
2. Load Python3.11 module.
3. Create virtualenv.
4. Clone project from Gerrit.
5. Source virtualenv.
6. Install required python libraries using requirements.txt.
7. Create symbolic link to pre-commit githook:
```
ln -s .githooks/pre-commit .git/hooks/pre-commit
```

## Test execution in local environment
There are some environment variables required to set.

```
export PIPELINE=test_pipeline
export ENVIRONMENT=test_env
export NAMESPACE=test_ns

python main.py <job_name>
```
