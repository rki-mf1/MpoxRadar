# MpoxRadar-frontend
MpoxRadar is a worldwide interactive dashboard for genomic surveillance of mpox.

This application is a result of a collaboration between Hasso Plattner Institute and Robert-Koch Institute.

-------

MpoxSonar intregated under `pages/libs` (Git subtree)

# Installation (Debian/Ubuntu)

1. Prepare environment
```
sudo apt update && sudo apt upgrade

```

- 1.1. Setup the mariadb package (MariaDB Connector/C)
please see https://mariadb.com/docs/skysql/connect/programming-languages/c/install/#Installation_via_Package_Repository_(Linux) or in short
    ```
    wget https://r.mariadb.com/downloads/mariadb_repo_setup
    chmod +x mariadb_repo_setup

    # be careful on the mariadb version "mariadb-10.6.XX"
    sudo ./mariadb_repo_setup --mariadb-server-version="mariadb-10.6.10"

    sudo apt install libmariadb3 libmariadb-dev
    ```

2. Clone this project
```
git clone https://github.com/ferbsx/MPXRadar-frontend.git
```
3. We use conda package manager (also work with [mamba](https://mamba.readthedocs.io/en/latest/installation.html)) to initiate python environment.
```
# prepare conda channels, if never run these before
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge
conda config --set channel_priority strict

conda create -n mpxradar python=3.10 poetry fortran-compiler emboss=6.6.0
conda activate mpxradar
```
4. Next, we use [poetry](https://python-poetry.org/docs/basic-usage/) to install/manage dependencies of the project.
```
cd MPXRadar-frontend
poetry install
```
5. By default, MPXSonar expects the file ".env" and is located in the current root directory. Please change the example ".env.template" to ".env".
```
cp .env.template .env
```
The ".env" variable can then be set according to the environment.

# Start App.

Right now we can start application by using below command.
```
python app.py
```

----


To run the application with a specific database ```mpox_testdata``` (or another database) on ```127.0.0.1``` (or another HOST) and a specific ```<USER>```:
```
MYSQL_HOST=127.0.0.1 MYSQL_USER=<USER> MYSQL_PW= MYSQL_DB=mpox_testdata python app.py
```
