# -- Project information -------------------------------------------------------

import importlib.metadata
import os

project = "plotstyle"
author = "Rahul Kaushal"
copyright = "2026, Rahul Kaushal"

release = importlib.metadata.version("plotstyle")
version = ".".join(release.split(".")[:2])

# -- General configuration -----------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "myst_parser",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- MyST (Markdown) settings --------------------------------------------------

myst_enable_extensions = [
    "colon_fence",
    "fieldlist",
    "deflist",
]
myst_heading_anchors = 3

# -- Autodoc / autosummary settings --------------------------------------------

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autosummary_generate = True

# -- Napoleon (NumPy + Google docstring) settings ------------------------------

napoleon_numpy_docstring = True
napoleon_google_docstring = True  # hybrid style: Args: (Google) + Returns/Raises (NumPy)
napoleon_use_rtype = False
napoleon_use_param = True
napoleon_preprocess_types = True

# -- Intersphinx ---------------------------------------------------------------

intersphinx_mapping: dict = {
    "python": ("https://docs.python.org/3", None),
}

# External inventories require trusted TLS; on RTD this always works.
# Local builds behind corporate proxies may fail, so we only enable
# the full set when running on RTD or when INTERSPHINX_FULL is set.
if os.environ.get("READTHEDOCS") or os.environ.get("INTERSPHINX_FULL"):
    intersphinx_mapping.update(
        {
            "matplotlib": ("https://matplotlib.org/stable/", None),
            "numpy": ("https://numpy.org/doc/stable/", None),
            "seaborn": ("https://seaborn.pydata.org/", None),
        }
    )

intersphinx_timeout = 5  # seconds; avoids long hangs behind proxies

# -- Suppress warnings ---------------------------------------------------------

suppress_warnings = [
    # Benign RST formatting in auto-generated content from autodoc + napoleon
    # for frozen dataclass attribute sections.  Does not affect HTML output.
    "docutils",
]

# -- HTML theme ----------------------------------------------------------------

html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "source_repository": "https://github.com/rahulkaushal04/plotstyle",
    "source_branch": "main",
    "source_directory": "docs/",
}

# -- Source suffix -------------------------------------------------------------

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
