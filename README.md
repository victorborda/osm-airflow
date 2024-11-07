# osm-airflow
Use Apache Airflow to perform ETL of OSM data

## Airflow setup for local Mac development:

1. Set this value in your .zshrc file:

```bash
export AIRFLOW_HOME=~/airflow
```

or whatever suits your fancy.

From here down run commands in this directory after having run
```bash
source ./venv/bin/activate
```

2. Run the following commands just once:

```bash
airflow db init
airflow users create --username admin --password <password> --firstname <yourfirstname> --lastname <yourlastname> --role Admin --email <youremail>
```

3. Run these to actually start the airflow webserver and scheduler (any non-conflicting port is fine):

```bash
airflow webserver --port 8090 > webserver.log 2>&1 &
airflow scheduler > scheduler.log 2>&1 &
```

Once running, you can access the Airflow UI at http://localhost:8090/

You will want to run the osm_etl.py dag.

## Deeper Dive

Okay, but what are we doing here and why? 

### OSM2PGSQL

Osm2pgsql is used to import OSM (OpenStreetMap) data into a PostgreSQL/PostGIS database for rendering into maps and many other uses. Usually it is only part of a toolchain. For instance other software is needed for the actual rendering (i.e. turning the data into a map, like Prettymapp or Mapnik) or delivery of the maps to the user (MapLibre.js for instance). Osm2Pgsql is flexible and needs to be steered so that its output ends up in PostGis in an optimal way - see the PgOsmFlex section below.

It dumps a sql file out which we just then load into the actual postgis databasde that bandiwalk uses.

<https://osm2pgsql.org/doc/manual.html#the-flex-output>

An important part of what osm2pgsql does is creating geometries from OSM data. In OSM, only nodes have a location, ways get their geometry from member nodes and relations get their geometry from member nodes and ways. Osm2pgsql assembles all the data from the related objects into valid geometries.

The geometry types supported by PostGIS are from the Simple Features defined by the OpenGIS Consortium (OGC).

For running on MacOS you can do this:
>brew install osm2pgsql

But using the AirFlow dag in this repo is a little better as it allows you to just use the existing docker image which includes osm2pgsql and pgosmflex (below).

To actually build osm2pgsql requires a decently extensive amount of dependent library and cmake setup. In that way, not too dissimilar from MetaGraph. For the moment though, and actually probably longterm, PgOsmFlex does all the hard lifting and there is a docker image available that contains osm2pgsql, pgosmflex, and postgis, so just use that to do all the cleaning and loading. 

### PGOSMFLEX

This excellent tool uses OSM2PGSQL to import OSM data into PostGis. It uses the Flex output capabilities of OSM2PGSQL to transform the data and improve the table and column setup (including indexes). The idea is to use PGOSMFLEX to coordinate and drive the process, and then have it do a sql dump output. Then you take that output and load it into your real PostGis database instance. To that end, PGOSMFLEX runs as a docker container with both Pgosmflex and PostGis in it.

It's actually quite simple to use. Grab the image, run it, and issue one docker exec command.

These commands need data to operate on though, so you have to get your desired pbf files downloaded first (or let the importer download them for you). 

There is also a public github repo for PgOsmFlex here (but for most purposes, the docker image is sufficient):
<https://github.com/rustprooflabs/pgosm-flex/blob/main/Dockerfile>

PGOSMFLEX is built and maintained by RustProof Labs. Their guide to PgOsmFlex is here:
<https://pgosm-flex.com/quick-start.html>

They also have an excellent book on PostGIS and OSM:
<https://blog.rustprooflabs.com/2022/10/announce-mastering-postgis-openstreetmap>