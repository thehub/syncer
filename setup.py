from setuptools import setup, find_packages

setup(name='syncer',
      version='0.5.2',
      packages=find_packages(),
      install_requires=[
           "Pyro",
           "Elixir",
           "mechanize"
      ],
      dependency_links = [
            "http://nchc.dl.sourceforge.net/sourceforge/pyro/Pyro-3.9.1.tar.gz",
      ]
      )
