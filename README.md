# MpoxRadar-frontend
MpoxRadar is a worldwide interactive dashboard for genomic surveillance of mpox.

This application is a result of a collaboration between Hasso Plattner Institute and Robert-Koch Institute.

-------

MpoxSonar intregated under `pages/libs` (Git subtree)

# Installation
1. Clone this project
```
git clone https://github.com/ferbsx/MPXRadar-frontend.git
```
2. We use conda package manager (also work with [mamba](https://mamba.readthedocs.io/en/latest/installation.html)) to initiate python environment.
```
conda create -n mpxradar python=3.9 poetry fortran-compiler emboss=6.6.0
conda activate mpxradar
```
3. Next, we use [poetry](https://python-poetry.org/docs/basic-usage/) to install/manage dependencies of the project.
```
cd MPXRadar-frontend
poetry install
```
4. By default, MPXSonar expects the file ".env" and is located in the current root directory. Please change the example ".env.template" to ".env".
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

Quick Demo, please run below.
```
python example.app.py
```


----

To run the application with a specific database ```mpox_testdata``` (or another database) on ```127.0.0.1``` (or another HOST) and a specific ```<USER>```:
```
MYSQL_HOST=127.0.0.1 MYSQL_USER=<USER> MYSQL_PW= MYSQL_DB=mpox_testdata python app.py
```
