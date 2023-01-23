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
- Pictures: data associated to monuments pictures, both WLM photos and Wikidata Images (property P18)
- Categories: categories of queries of monuments, related to the SPARQL queries used for data scraping

**Geographic entites**:

- Italian Regions, provinces and municipalitites (with geographic boundaries)

**Scraping support entites**:

- Snapshots
- Snapshot categories, corresponding to the SPARQL queries configured in the project

## APIs

The REST APIs are developed using `django-rest-framework` and follow the project conventions.
All the apis are public.

Once the project is installed on a server or running locally, a web page with a "swagger" interface is exposed at the url:

`/api/schema/swagger-ui/`

## Data scraping

One of the feature of the server application is related to the periodic data scraping task from pubic wiki apis, in order to populate and update the project database.

The scraping procedure is based on a set of SPARQL queries, that gather a list of interesting entities from wikipedia (monuments in our case), based on geographical and categorical filters. Each query is associated with a monument category. The SPARQL tries to gather as much metadata as possible, but the information related to images must be fetched by query the Wikipedia REST API, for each monument in the list

The snapshot procedure works as follows:

- when the procedure starts, a "Snapshot" record is created, and marked as "not complete"
- for each SPARQL query registered in the system, the related category, if not existing, is created in the database
- each SPARQL is run and the results are stored in the database, as JSON data representing a list of monuments
- once all the SPARQL queries are run, for each query:
  - for each monument in the results list: if the monument was not updated during the current snapshot we perform a specific query against the REST api, in order to gather images information. and the SPARQL query category is annotated on the monument. If the monument data was already fetched during the current snapshot, the REST api query is skipped and the SPARQL query category is annotated on the monument.
- once all monuments for a category have been processed, the query is marked as "complete"
- once all the category have been processed, the snapshot is marked as "complete"

The snapshot task is quite expensive (about 130k monuments as of January 2023) and is implemented as a "long-running" task. The system is setup to continue the last snapshot is the job is interrupted. The implementation allows only one snapshot a time. With the current deploy configuration this is guaranteed to be true, as only a single worker is allocated by the docker-compose file used in production.

There are two kind of SPARQL queries in the project: specific and categorical queries.
All the queries must produce items with a fixed structure (refer to the existing queries).

## SPARQL queries extensions
The implementation of the data scraping feature allows to extend the SPARQL queries in the system with a minimal modification to the codebase. The procedure is different for the two types of queries present in the codebase, that are described in the following sections.

### Specific SPARQL queries

This set of SPARQL queries was setup to address specific filters and are self contained, i.e. the don't need any parameter to be run. They are contained in the following files:

- `server/wlm/main/SPARQL-contest.txt`
- `server/wlm/main/SPARQL-fortifications.txt`
- `server/wlm/main/SPARQL-municipalities-views.txt`

In order to extend the system to add more of these queries, the costant `WLM_QUERIES` in the file server/wlm/main/wiki_api.py must be changed, and the relative text file containing the query must be added to the project.

### Categorical SPARQL queries

There is another type of queries setup in the system, based on a single SPARQL query defined to gather monuments pertaining to a specific Wikipedia category, expressed by a `Q number`
Such query is described in the file:

- `server/wlm/main/SPARQL-typologies.txt`

In this file, the symbol `wd:Q_NUMBER_TYPE` must be replaced with the actual Q number referring to the category we want to search. These categories and the replacement are handled automatically by the project.

In order to extend the categories for which the query is run, the following file must be edited:

- `wlm/main/WIKI_CANDIDATE_TYPES.csv`

This file is a csv containing a row for each category, with the attributes q_number,label,group that must be provided.

# Local development

The project is based on a standard Django application. To develop locally we provide also a `docker-compose` file for the database and cache services.

In order to develop locally:

- clone the repository
- create a python environment based on the file `server/requirements.txt `
- install docker and docker-compose locally
- start the docker-compose.yml by issuing the command `docker-compose up` in the server folder
- open a shell in the server/wlm folder of the project and run the following commands:
  - `python manage.py migrate`
  - `python manage.py createsupersuer`
    (this command is interactive and will ask for username and password to be used to access the site)
  - `python manage.py runserver`
    (this command should start a local webserver)
  - open a browser to the url `http://localhost:8000/admin`. You should see a login interface and if you enter the credentials previously set with the `createsuperuser` command, you should be able to login and see the "admin" interface.

# Installation

Here we describe the installation process based on docker and docker compose.

## Install docker and prepare the filesystem

1. Install docker (https://docs.docker.com/get-docker/)
2. Install docker-compose (https://docs.docker.com/compose/install/other/) or the docker "compose" plugin (https://docs.docker.com/compose/install/linux/)
3. Create a target folder for the application files on the server. In our case we'll use the `/srv/wlm-it-app/` folder
4. Copy all files from the "deploy_docker" folder of the repo to our target folder.

At the end of these steps, you should:

- be able to run the "docker-compose ps" command
- have the files "docker-compose.yml", "localsettings.py" and "nginx.conf" in your `/srv/wlm-it-app/` folder

## Login to docker, pull the docker-compose stack and start the services

docker login -u wikimediait

docker-compose pull

docker-compose up -d

You should get logs about container starting on the server.
To inspect what's going on you can type:

docker-compose logs --follow

and inspect the logs of the various services of the stack.

**Note**: the docker-compose stack is configured to bind the port 80 of the internal webserver (nginx) to the port 80 of the host server.
Be sure to stop any service running on port 80 (such as Apache or other webservers that may already be installed on the server).

## Creating a superuser for the admin section

docker-compose exec wlm_server bash

python manage.py createsuperuser

Enter a desired username and the related password in order to obtain an administrative access to the "admin" section,
which you'll use to schedule the scraping process.

## Importing geo layers

The application uses ISTAT data for handling visualization and lookups of data.

In order to provide geographic based lookups and aggregations, the application must be initialized with the italian administrative borders, at 3 levels (regions, provinces and municipalities).
The municipal borders are imported with two different of detail, one used for geographic lookups (to identify municipality of a monument from its coordinates) and one used for rendering the borders in the client application

The geographic layers should be provided as shapefiles with the structure described here:

https://www.istat.it/it/files//2018/10/Descrizione-dei-dati-geografici-2020-03-19.pdf

At the moment, the application has been initialized with the files available at these links, updated ad 01 january 2022:

- Simplified borders: https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/Limiti01012022_g.zip
- Detailed borders: https://www.istat.it/storage/cartografia/confini_amministrativi/non_generalizzati/Limiti01012022.zip

There is a utility script that downloads and imports the data from the links described above

`sh default_geo.sh`

If the files are already on the filesystem or we want to import custom shapefile, the `update_geo` management command is available, with the following syntax:

usage: manage.py update_geo [-h] [--dry-run] [--version] [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH]
[--traceback] [--no-color] [--force-color] [--skip-checks]
regions_path provinces_path municipalities_path municipalities_lookup_path

(Updates geo data and link from monuments to municipalities)

positional arguments:
- regions_path
- provinces_path
- municipalities_path
- municipalities_lookup_path

## Admin interface

The django "admin" interface can be used to schedule the snapshots and to inspect the snapshot progress and the database in general. It is based on a standard interface that lists entities on the left and provides a list+detail interface for all the entities.

### Authentication and authorization

#### Users and groups

These area standard entities available in django. The "Groups" feature is not used, while the "Users" section can be used to configure new users enabling access to the admin interface.
In order to create users with full access to the system, the flags "STAFF" and "SUPERUSER" must be enabled.

### CRON_TOOLS

This is custom django app implemented for the snapshot scheduling. The only entity related to this app is the "Job", which represents a scheduled long-running task.

Il allows to enter scheduling in two ways:

- by entering an unix cron like syntax (for recurring jobs) ([https://en.wikipedia.org/wiki/Cron](https://en.wikipedia.org/wiki/Cron))
- by specifying date and time for single runs

To create a new schedule: click on the "add job" button in the top right.
A form is presented, and the following fields must be filled:

- The field **Job type**: must be set to the string `take_snapshot_reset_pics`
- One of the fields **Excecution time** or **Cron expression** must be filled for one-shot or recurring snapshots

A very useful tool that may help in writing and reading cron expression is available at https://crontab.guru/

### DJANGO_RQ

This is a section provided by `rq`, the library we use for the long-running jobs implementation in django. Il exposes a single entity, the "Queues" that show which jobs are scheduled and their state.

### MAIN

Under the section "Main" are listed the domain specific entites of the project.
These are all the entities described in the "Database structure" section.
The admin may be useful for inspecting such entities for debugging purpose.

This section may also be used to inspect the snapshot process, by looking at the following pages:

- `Snapshots` will show all the snapshots in the system, with their completion state.
- `Category snapshots` is the temporary entity used to track and resume the snapshot procedure. Once the snapshot is complete the category snapshots should be empty, but when a snapshot is running you should see a list of all the categories defined by SPARQL queries with their completion state. The actual query is also present in the interface

The `Monuments` and `Pictures` sections contain the actual data served by the rest API.
