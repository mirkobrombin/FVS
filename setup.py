from setuptools import setup

setup(
    name='FVS',
    version='0.2',
    packages=['fvs'],
    url='https://github.com/mirkobrombin/FVS',
    license='MIT',
    author='Mirko Brombin',
    author_email='send@mirko.pm',
    description='File Versioning System with hash comparison, deduplication and data storage to create unlinked '
                'states that can be deleted ',
    entry_points={
        'console_scripts': [
            'fvs=fvs.cli:fvs_cli'
        ]
    },
    install_requires=[
        'orjson'
    ]
)
