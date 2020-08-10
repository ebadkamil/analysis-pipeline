import os.path as osp
import re
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


def find_version():
    with open(osp.join('analysis', '__init__.py'), 'r') as f:
        match = re.search(r'^__version__ = "(\d+\.\d+\.\d+)"', f.read(), re.M)
        if match is not None:
            return match.group(1)
        raise RuntimeError("Unable to find version string.")


setup(name="analysis-pipeline",
      version=find_version(),
      author="Ebad Kamil",
      author_email="kamilebad@gmail.com",
      maintainer="Ebad Kamil",
      packages=find_packages(),
      entry_points={
          "console_scripts": [
              "start_pipeline = analysis.application:start_pipeline",
              "start_test_client = analysis.application:start_test_client"
          ],
      },
      install_requires=[
           'pyFAI>0.16.0',
           'redis',
           'pyzmq',
           'psutil'
      ],
      extras_require={
        'test': [
          'pytest',
        ]
      },
      python_requires='>=3.6',
)
