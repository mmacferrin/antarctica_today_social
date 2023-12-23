"""Code for updating the root README.md with the last date of the update."""

import datetime
import os
import re

def substitute_date_in_readme():
    """Put the latest date (datestr as a YYYY.MM.DD format) into the main README.md file.

    The date string is from the file /images/most_recent_date.txt.
    This shoudl be run at the end of creating a new post in anttoday_social.py.

    Returns True if the README.md was changed at all. False otherwise.
    """

    # Fetch the latest date string from "most_recent_date.txt"
    date_fname = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "images", "most_recent_date.txt"))
    assert os.path.exists(date_fname)
    date_str = open(date_fname, 'r').read().strip()
    assert re.search(r"\A\d{4}\.\d{2}\.\d{2}", date_str) is not None

    # Create a pretty version of the date string.
    date_str_pretty = datetime.datetime.strptime(date_str, "%Y.%m.%d").strftime("%A, %B %-m, %Y")

    readme_fname = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))
    # Make sure the README file is actually there.
    assert os.path.exists(readme_fname)

    # Read the README.md in lines:
    lines = open(readme_fname, 'r').readlines()
    lines_out = lines.copy()

    date_start_comment = r'<!--date_start-->'
    date_end_comment = r'<!--date_end-->'

    for i, line in enumerate(lines):
        # Look for both the start and end date tags.
        date_start_match = re.search(date_start_comment, line)
        if date_start_match is None:
            continue
        else:
            date_end_match = re.search(date_end_comment, line)
            # If that date_start string is in the line, the date_end string should be too.
            if date_end_match is None:
                print("WARNING: String '{0}' found on line {1} of README.md without '{2}'. Skipping.".format(
                    date_start_comment,
                    i + 1,
                    date_end_comment
                ))
                continue

        # If we've gotten here, we have a matching line.
        # print("Line", i + 1, date_start_match, date_end_match)
        # print(line[date_start_match.span()[1] : date_end_match.span()[0]])

        # Get the start text on the line (before the date):
        line_start = line[:date_start_match.span()[1]]
        line_end = line[date_end_match.span()[0]:]

        # Create the new line with the new date string in there.
        line_out = line_start + date_str_pretty + line_end
        # Swap the line in the file with the new line we just created.
        lines_out[i] = line_out

    # If no lines were actually changed, at all, we can just say that and don't bother re-writing the file.
    numlines_changed = 0
    for l1, l2 in zip(lines, lines_out):
        if l1 != l2:
            numlines_changed += 1

    if numlines_changed == 0:
        print(os.path.basename(readme_fname), "not modified. No changes made.")
        return False

    # Output the new lines to the README file.
    open(readme_fname, 'w').writelines(lines_out)
    assert os.path.exists(readme_fname)

    print(os.path.basename(readme_fname), "updated with '{0}', {1} lines modified.".format(date_str_pretty,
                                                                                           numlines_changed))

    return True


if __name__ == "__main__":
    substitute_date_in_readme()