"""Code for updating the root README.md with the last date of the update."""

import datetime
import os
import re

def substitute_date_in_readme(date_str):
    """Put the latest date (provided in datestr as a YYYY.MM.DD format) into the main README.md file."""

    readme_fname = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))
    # Make sure the README file is actually there.
    assert os.path.exists(readme_fname)

    # Read the README.md in lines:
    lines = open(readme_fname, 'r').readlines()
    lines_out = lines.copy()

    date_start_comment = r'<!--start_date-->'

    for i, line in lines:
