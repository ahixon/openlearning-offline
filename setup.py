from setuptools import setup, find_packages
#import os

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
#def read(fname):
    #return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "ol-offline",
    version = "0.1.0",

    install_requires = ['BeautifulSoup >= 3.2'],

    author = "Alex Hixon",
    author_email = "alex@alexhixon.com",

    description = ("Allows you to mark and manage OpenLearning submissions locally."),
    license = "MIT",
    keywords = "openlearning marking web",
    url = "https://github.com/ahixon/openlearning-offline",

    packages = find_packages (),
    scripts = ['ol.py', 'ol-sms.py'],

    #long_description = read('README'),
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
)
