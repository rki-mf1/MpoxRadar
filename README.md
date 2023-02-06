# MpoxRadar-frontend
MpoxRadar is a worldwide interactive dashboard for genomic surveillance of Mpox (Monkeypox virus).

This application is a result of a collaboration between Hasso Plattner Institute and Robert-Koch Institute.

-------

MpoxSonar intregated under `pages/libs` (Git subtree)

# Installation (Debian/Ubuntu)

## Prepare environment.

0. Install all requried softwares
```
sudo apt update && sudo apt upgrade
sudo apt install mariadb-server mariadb-client
sudo apt-get install redis

```

1. Prepare MariaDB server
```
sudo mysql_secure_installation

```
⚠️ for more detail ["mysql_secure_installation"](https://mariadb.com/kb/en/mysql_secure_installation/). (Optional) Create an account (non-root) with password authentication

2. Prepare MariaDB connector

```
wget https://r.mariadb.com/downloads/mariadb_repo_setup
chmod +x mariadb_repo_setup

# be careful on the mariadb version "mariadb-10.6.XX" that was installed on your machine.
sudo ./mariadb_repo_setup --mariadb-server-version="mariadb-10.6.10"

sudo apt install libmariadb3 libmariadb-dev
```
please see https://mariadb.com/docs/skysql/connect/programming-languages/c/install/#Installation_via_Package_Repository_(Linux)

3. Setup Redis server.
```
# Run
redis-server /etc/redis/redis.conf
# check redis-server
ps aux | grep redis-server
```
⚠️ please edit "/etc/redis/redis.conf" for your server configuration.


## Setup application.

1. Clone this project
```
git clone https://github.com/rki-mf1/MpoxRadar
```

2. We use conda package manager (also work with [mamba](https://mamba.readthedocs.io/en/latest/installation.html)) to initiate python environment.
```
# prepare conda channels, if never run these before
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge
conda config --set channel_priority strict

conda create -n mpxradar python=3.10 poetry fortran-compiler emboss=6.6.0
conda activate mpxradar
```

3. Next, we use [poetry](https://python-poetry.org/docs/basic-usage/) to install/manage dependencies of the project.
```
cd MPXRadar-frontend
poetry install
```

4. By default, the project expects the ".env" file and it must be located in the project root directory.
Please copy the template ".env.template" to ".env".
```
cp .env.template .env
```
The ".env" variables can then be set according to your environment.

# Start App.

Right now we can start application by using below command.
```
python app.py
```

----

# For production use.

1. Gunicorn
2. Nginx

----

⚠️ The work is still ongoing 🏗️ ⚠️

If you have found any bugs or technical problems with the application, report them in the Issues repository.

For business inquiries or professional support requests 🍺,
please contact Prof. Dr. Bernhard Renard (bernhard.renard@hpi.de) or Dr. Stephan Fuchs (fuchsS@rki.de)
