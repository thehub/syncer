from setuptools import setup, find_packages

setup(name='syncer',
      version='0.2',
      packages=find_packages(),
      install_requires=[
           "pyro",
           "Elixir",
      ]
      )
