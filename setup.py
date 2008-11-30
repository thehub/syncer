from setuptools import setup, find_packages

setup(name='syncer',
      version='0.2',
      packages=find_packages(),
      install_requires=[
           "Pyro",
           "Elixir",
      ],
      dependency_links = [
            "http://downloads.sourceforge.net/pyro/Pyro-3.8.tar.gz?modtime=1219451921&big_mirror=0"
      ]
      )
