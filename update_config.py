#!/usr/bin/env python3

import difflib
import json
import os
import random
import string
import sys
import yaml

CONFIG = json.load(open('config/config.json'))

HEADER = '# This file is generated by update_config.py\n\n'


def Add(compose, name):
  compose[name] = {
    'build': name,
    'links': ['master'],
    'volumes': ['./config:/config'],
    'volumes_from': ['volumes'],
    'privileged': 'false',
  }


def CreatePassword():
  return ''.join(
      random.choice(string.ascii_letters + string.digits)
      for _ in range(16))


def WriteComposeYaml():
  compose = {
    'master': {
      'build': 'master',
      'ports': [
        '8010:8010',
        '9989:9989',
      ],
      'volumes': [
        './config:/config',
        '/srv/www/htdocs/builds:/srv/www/htdocs/builds',
      ],
      'volumes_from': ['volumes'],
    },
    'volumes': {
      'command': '/bin/true',
      'image': 'opensuse/tumbleweed',
      'volumes': ['/persistent-data'],
    }
  }

  for distro, versions in CONFIG['linux'].items():
    for version in versions:
      Add(compose, str('worker-%s-%s' % (distro, version)))

  for worker in CONFIG['special_workers']:
    Add(compose, str('worker-' + worker))

  with open('docker-compose.yml', 'w') as fh:
    fh.write(HEADER)
    yaml.dump(compose, fh, indent=2)
  print('Wrote docker-compose.yml')


def WritePasswords():
  workers = []
  workers.extend(CONFIG['special_workers'])
  for distro, versions in CONFIG['linux'].items():
    for version in versions:
      workers.append('%s-%s' % (distro, version))

  passwords = {name: CreatePassword() for name in workers}

  with open('config/secret/passwords.json', 'w') as fh:
    json.dump(passwords, fh, indent=2, sort_keys=True)
  print('Wrote config/secret/passwords.json')


def main():
  WriteComposeYaml()
  WritePasswords()


if __name__ == '__main__':
  main()
