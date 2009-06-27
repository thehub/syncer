from setuptools import setup, find_packages

setup(name='syncer',
      version='0.5.1',
      packages=find_packages(),
      install_requires=[
           "Pyro",
           "Elixir",
           "mechanize"
      ],
      )
