# Configuration file for the Sphinx documentation builder.

# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Project information
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath('../src'))

project = 'Ezcord'
copyright = '2023, tibue99'
author = 'tibue99'
release = '0.1.0'


# General configuration
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
]

always_document_param_types = True
simplify_optional_unions = True

autodoc_member_order = "bysource"

intersphinx_mapping = {
    "py": ("https://docs.python.org/3", None),
    "aio": ("https://docs.aiohttp.org/en/stable/", None),
    "req": ("https://requests.readthedocs.io/en/latest/", None),
    "dc": ("https://docs.pycord.dev/en/stable/", None),
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# Options for HTML output and furo customisation
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# https://pradyunsg.me/furo/customisation/

html_theme = 'furo'
html_static_path = ['_static']

html_title = f"<h3 align='center'>{release}</h3>"
html_logo = "_static/ezcord.png"
html_favicon = "_static/favicon.ico"
