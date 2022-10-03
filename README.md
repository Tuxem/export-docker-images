# export-docker-images
Script to export docker images from a name or docker-compose.yml.

If no tag is specified, the script look for associated tag version to know which one you export.

## Dependencies

### Packages

* python

### Python module
* docker
* click

## Usage

Without version (using latest)

```
./export_dockers.py --name influxdb
```

With specific version
```
./export_dockers.py --name influxdb:2.0.4
```

Export all images needed on a docker-compose.yml file
```
./export_dockers.py --dockercompose /home/myself/myapp/docker-compose.yml
```
