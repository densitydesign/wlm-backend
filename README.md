# Project structure

The WLM visualization backend is a server web application with the following purposes:

- Defines a data model and the SQL database structure
- Schedule and run a data scraping process that periodically updates WLM data
- Provides a REST api to access data from the web frontend

The application is based on the python language and the "django" web framework (https://www.djangoproject.com/)

The application has no public user interface, but exposes a web-based administrative interface used for configuration and database inspection purposes.

# Project dependecies and application stack

The django web application depends on the following services:

- A PostgreSQL relational database used for data persistence.
- A Redis key-value store used for caching and inter-process communication.

All the stack with the described dependencies is provided as a set of Docker images, deployed with `docker-compose` on a single server. 


# Django project structure

The django project is composed of two "applications", the modular units of the django frameworks:
- The `main` application: that contains the described data model and the related business logic (api and scraping)
- The `cron_tools` application, an utility application used to schedule long-running processes based on a cron-like syntax

All the project requirements are listed in the `requirements.txt` file

The application is also based on the following third-parties applications:

- django rest framework: use as the REST api framework
- django rq: used for running the periodic snapshot process in background 

The project follows the default template provided by django v4.x.
In the following subsections we'll describe briefly the project architecture.


## Database structure

The database structure is declared and managed by django, please refer to the `models.py` file for a complete description of the fields and tables used.
To summarize, the database handles the following entities:

**Application domain entites**:
- Monuments: the main entiry that is visualized in the frontend
- Pictures: data associated to monuments pictures (both wlm and mediawiki)
- Categories: categories of queries of monuments, related to the SPARQL queries used for data scraping

**Geographic entites**:
- Italian Regions, provinces and municipalitites (with geographic boundaries)

**Scraping support entites**:
- Snapshots
- Snapshot categories, corresponding to the SPARQL queries configured in the project

## APIs

The REST APIs are developed using `django-rest-framework` and follow the project conventions.
...
TODO: 
- intro
- link to swagger

## Data scraping

...
TODO: 
- explain how data scraping happens (sparql + wiki)
- sparql query configuration in codebase

# Development
TODO:
- explain how to start the project locally


# Installation
Here we describe the installation process based on docker and docker compose.

## Install docker and prepare the filesystem

1. Install docker (https://docs.docker.com/get-docker/)
2. Install docker-compose (https://docs.docker.com/compose/install/other/) or the docker "compose" plugin (https://docs.docker.com/compose/install/linux/)
3. Create a target folder for the application files on the server. In our case we'll use the `/srv/wlm-it-app/' folder
4. Copy all files from the "deploy_docker" folder of the repo to our target folder. 

At the end of these steps, you should:
- be able to run the "docker-compose ps" command
- have the files "docker-compose.yml", "localsettings.py" and "nginx.conf" in your `/srv/wlm-it-app/' folder


## Login to docker, pull the docker-compose stack and start the services
docker login docker.inmagik.com

docker-compose pull

docker-compose up -d

You should get logs about container starting on the server.
To inspect what's going on you can type:

docker-compose logs --follow

and inspect the logs of the various services of the stack.

**Note**: the docker-compose stack is configured to bind the port 80 of the internal webserver (nginx) to the port 80 of the host server.
Be sure to stop any service running on port 80 (such as Apache or other webservers that may already be installed on the server).


## Creating a superuser
docker-compose exec wlm_server bash

python manage.py createsuperuser

Enter a desired username and the related password in order to obtain an administrative access to the "admin" section,
which you'll use to schedule the scraping process.

## importing geo layers

In order to provide geographic based lookups and aggregations, the application must be initialized with the italian administrative borders, at 3 levels (regions, provinces and municipalities).
The municipal borders are imported with two different of detail, one used for geographic lookups (to identify municipality of a monument from its coordinates) and one used for rendering the borders in the client application

The geographic layers should be provided as shapefiles with the structure described here:

https://www.istat.it/it/files//2018/10/Descrizione-dei-dati-geografici-2020-03-19.pdf

At the moment, the application has been initialized with the files available at these links, updated ad 01 january 2022:
- Simplified borders: https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/Limiti01012022_g.zip
- Detailed borders: https://www.istat.it/storage/cartografia/confini_amministrativi/non_generalizzati/Limiti01012022.zip

There is a utility script that downloads and imports the data from the links described above

sh default_geo.sh

If the files are already on the filesystem or we want to import custom shapefile, the `update_geo` management command is available, with the following syntax:

usage: manage.py update_geo [-h] [--dry-run] [--version] [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH]
                            [--traceback] [--no-color] [--force-color] [--skip-checks]
                            regions_path provinces_path municipalities_path municipalities_lookup_path

(Updates geo data and link from monuments to municipalities)

positional arguments:
  regions_path
  provinces_path
  municipalities_path
  municipalities_lookup_path

## Snapshot jobs configuration
TODO:
- scheduling 


