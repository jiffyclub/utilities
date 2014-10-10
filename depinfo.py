#!/usr/bin/env python
"""
This script parses setup.py files for install_requires and extras_require
lists, parses the library names and version from those lists,
then queries PyPI for info about the libraries.

This prints lines like a CSV file with columns:

name,license1,license2,pypi_url

(There are two possible places to identify the library license in the
metadata so this provides both. One or both may be missing.)

"""

import argparse
import csv
import sys

import re
import requests
import toolz


def strip_comments(line):
    """
    Remove comments from a line of text.
    A line that is only a comment will come back as ''.

    """
    idx = line.find('#')

    if idx != -1:
        line = line[:idx] + '\n'

    return line


def parse_deps(f):
    """
    Parse dependencies from a single setup.py file.

    """
    setup = ''.join(strip_comments(l) for l in f)
    setup = re.sub(r'\s', '', setup)
    install_reqs = re.search(r'install_requires=\[(.+?)\],', setup)
    extra_reqs = re.findall(r'extras_require=\{.*\[(.+?)\].*\}', setup)

    if install_reqs:
        install_reqs = install_reqs.groups(1)[0].split(',')
    else:
        install_reqs = []

    extra_reqs = toolz.concat(e.split(',') for e in extra_reqs)

    return (
        s for s in (ss.strip('\'"') for ss in toolz.concatv(
            install_reqs, extra_reqs))
        if s)


def find_deps(files):
    """
    Parse a list of dependencies from a set of setup.py files.

    """
    return toolz.unique(toolz.concat(parse_deps(f) for f in files))


def get_info(lib):
    """
    Retrieve info about a libray from PyPI.

    """
    version_comp = re.search(r'([=<>])', lib)

    if version_comp:
        comp = version_comp.groups(1)
        name = lib[:version_comp.start()]
        if '>' not in comp:
            version = lib[version_comp.end():]
        else:
            version = None
    else:
        name = lib
        version = None

    # drop the [redis] part of things like celery[redis]
    if '[' in name:
        name = name[:name.index('[')]

    if version:
        url = 'http://pypi.python.org/pypi/{}/{}/json'.format(name, version)
    else:
        url = 'http://pypi.python.org/pypi/{}/json'.format(name)

    json = requests.get(url).json()

    license = [
        s for s in json['info']['classifiers'] if s.startswith('License')]

    license = license[0] if license else ''

    return (
        name, json['info']['license'], license,
        'http://pypi.python.org/pypi/{}'.format(name))


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description=(
            'Generate a list of dependencies by parsing a '
            'set of setup.py files'))
    parser.add_argument(
        'files', type=argparse.FileType('r'), nargs='+',
        help='setup.py files to parse for dependencies.')
    return parser.parse_args(args)


def main(args=None):
    args = parse_args(args)
    deps = find_deps(args.files)

    info = (get_info(d) for d in deps)

    writer = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)

    for i in info:
        writer.writerow(i)

if __name__ == '__main__':
    sys.exit(main())
