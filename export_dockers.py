#!/bin/env python3
"""
Script to fetch dockers from docker hub and export
"""

from sys import exit
from os import path, makedirs, chmod
import logging
import time
import requests

import click
import docker


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
DEFAULT_CFG = 'config.ini'


def fetch_tags(index_url, image_name):
    if '/' in image_name:
        tags_url = '{}/v2/repositories/{}/tags/'.format(index_url, image_name)
    else:
        tags_url = '{}/v2/repositories/library/{}/tags/'.format(index_url, image_name)
    r = requests.get(tags_url)
    
    return r.json()['results']

def export_image(client, full_name, directory_output):
    tar_path = directory_output + '/' + full_name.replace('/', '-').replace(':', '-') + '.tar'

    if path.isfile(tar_path):
        answer = input(tar_path + ' already exists. Overwrite ? (y/N) ')
        if answer.upper() not in ['Y', 'YES', 'O', 'OUI']:
            return 3

    client.images.pull(full_name)

    image = client.images.get(full_name)

    logging.info('Exporting {} to {}'.format(full_name, tar_path))
    with open(tar_path, 'wb') as f:
        for chunk in image.save():
            f.write(chunk)

def get_arch_digest(images, arch):
    for image in images:
        if image['architecture'] == arch:
            return image['digest']

def get_image(client, index_url, name, directory_output):

    logging.info('Pulling {}...'.format(name))
    image = client.images.pull(name)

    # if version is already specified in container name
    if ":" in name:
        export_image(client, name, directory_output)
    # Otherwise, get latest and look for precise tag
    else:
        tags = fetch_tags(index_url, name)
      
        for tag in tags:
            if tag['name'] in ['latest', 'mainline']:
                latest_digest = get_arch_digest(tag['images'], 'amd64')
            else:
                digest = get_arch_digest(tag['images'], 'amd64')
                if latest_digest == digest:
                    full_name = name + ':' + tag['name']
                    export_image(client, full_name, directory_output)
                    return 0
        
        # if we arrive at this point, no match found between last and precise tag.
        use_next = False
        i = 1
        while not use_next:
            logging.warning('No precise version of {} matching with latest.'.format(name))
            answer = input('Export {}:{} ? [y/N] '.format(name, tags[i]['name']))
            if answer.upper() in ['Y', 'YES', 'O', 'OUI']:
                use_next = True
                full_name = name + ':' + tags[i]['name']
                export_image(client, full_name, directory_output)
            i += 1

def parse_dockerfile(dockerfile):
    names = []

    with open(dockerfile, 'r') as file:
        for l in file.readlines():
            if 'image:' in l:
                names.append(l.split('image: ')[1].replace('\n', ''))

    return names

@click.command()
@click.option('-n', '--name', help ='Name of the container to export. Ex : postgres')
@click.option('-d', '--directory-output', default='/tmp', help ='Path to the output directory to store dockers\'s tar')
@click.option('-f', '--dockercompose', help='path of docker-compose.yml to export containers from')  
@click.option('-i', '--index-url', default="https://hub.docker.com", help='Index URL')
@click.option('--verbose', is_flag=True)
def main(name, dockercompose, index_url, directory_output, verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    client = docker.from_env()

    if name:
        get_image(client, index_url, name, directory_output)
    elif dockercompose:
        docker_names = parse_dockerfile(dockercompose)

        for name in docker_names:
            get_image(client, index_url, name, directory_output)
    else:
        logging.error('One of --name or --dockerfile arguments must be used')

if __name__=="__main__":
    logger = logging.getLogger('cluster-users')

    main()
