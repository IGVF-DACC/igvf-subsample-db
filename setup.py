import os
import re
from pathlib import Path

import setuptools

META_PATH = Path('igvf_subsample_db', '__init__.py')
HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with Path(HERE, *parts).open(encoding='utf-8') as f:
        return f.read()


META_FILE = read(META_PATH)


def find_meta(meta):
    """
    Extract __*meta*__ from META_FILE.
    """
    meta_match = re.search(
        r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta), META_FILE, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise


with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='igvf-subsample-db',
    version=find_meta('version'),
    python_requires='>=3.6',
    scripts=[
        'bin/create_rule_template',
        'bin/get_subsampled_uuids',
        'bin/subsample_pg',
    ],
    author='Jin wook Lee',
    author_email='leepc12@gmail.com',
    description='This tool subsamples PG DB of IGVF/ENCODE server.',
    long_description=(
        'This tool subsamples PG DB of IGVF/ENCODE server based on a '
        'subsampling rule JSON file. Such JSON file defines minimum number '
        'of objects, subsampling rate and extra condition for each profile.'
    ),
    long_description_content_type='text/markdown',
    url='https://github.com/igvf-dacc/igvf-subsample-db',
    packages=setuptools.find_packages(exclude=['docs']),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
    ],
    install_requires=[
        'requests>=2.20',
        'psycopg2>=2.0.6',
    ],
)
