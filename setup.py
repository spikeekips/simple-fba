import sys  # noqa
import subprocess  # noqa
from setuptools import setup, find_packages


commit = subprocess.Popen(
    'git rev-parse --short HEAD'.split(),
    stdout=subprocess.PIPE,
).stdout.read().decode('utf-8').strip()

setup(
    name='simple-fba',
    version='0.2+%s' % commit,
    description='simple implementation and simulation of FBA',
    author='Spike^ekipS',
    author_email='spikeekips@gmail.com',
    license='GPLv3+',
    keywords='blockchain fba scp stellar quorum python byzantine agreement',
    install_requires=(
        'colorlog',
    ),
    package_dir={'': 'src'},
    packages=find_packages('src', exclude=('test',)),
    scripts=(
        'scripts/simple-fba-simulator.py',
    ),
    zip_safe=False,
)
