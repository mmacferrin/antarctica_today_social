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
    assert re.search(r"\A\d{4}\.\d{2}\.\d{2}\Z", date_str) is not None

    # Create a pretty version of the date string, e.g. "Saturday, December 23, 2023"
    date_str_pretty = datetime.datetime.strptime(date_str, "%Y.%m.%d").strftime("%A, %B %-d, %Y")

    readme_fname = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))
    # Make sure the README file is actually there.
    assert os.path.exists(readme_fname)

    # Read the README.md in lines:
    lines = open(readme_fname, 'r').readlines()
    lines_out = [""] * len(lines)

    date_long_start_comment = r'<!--date_long_start-->'
    date_long_end_comment = r'<!--date_long_end-->'

    date_short_start_comment = r'<!--contains_short_date_start-->'
    date_short_end_comment = r'<!--contains_short_date_end-->'

    for i, line in enumerate(lines):
        # Look for both the start and end date tags.
        date_long_start_match = re.search(date_long_start_comment, line)
        if date_long_start_match is not None:
            date_long_end_match = re.search(date_long_end_comment, line)
            # If that date_start string is in the line, the date_end string should be too.
            if date_long_end_match is None:
                print("WARNING: String '{0}' found on line {1} of README.md without '{2}'. Skipping.".format(
                    date_long_start_comment,
                    i + 1,
                    date_long_end_comment
                ))
            else:
                # Sanity check to make soure our logic checks out. Both these should be valid matches here.
                assert date_long_start_match is not None and date_long_end_match is not None
                # If we've gotten here, we have a matching line.
                # print("Line", i + 1, date_start_match, date_end_match)
                # print(line[date_start_match.span()[1] : date_end_match.span()[0]])

                # Get the start text on the line (before the date):
                line_start = line[:date_long_start_match.span()[1]]
                line_end = line[date_long_end_match.span()[0]:]

                # Create the new line with the new date string in there.
                line = line_start + date_str_pretty + line_end

        # Above we substituted the "pretty date" string if it existed. Now look for the other "short date" string.
        # It'll be between the date_short_start_comment and date_short_end_comment, and in the format YYYY.MM.DD
        # First, find the date_short_start_comment.
        date_short_start_match = re.search(date_short_start_comment, line)
        if date_short_start_match is not None:
            date_short_end_match = re.search(date_short_end_comment, line)

            # If that date_start string is in the line, the date_end string should be too.
            if date_short_end_match is None:
                print("WARNING: String '{0}' found on line {1} of README.md without '{2}':\n{3}\nSkipping.".format(
                    date_short_start_comment,
                    i + 1,
                    date_short_end_comment,
                    line.rstrip()
                ))
            else:
                # Cut out the span in which to search for the YYYY.MM.DD.
                # This is a bit different than above because we're just looking for a subset of the string
                # between the comments, not the whole string.
                line_subset = line[date_short_start_match.span()[1]:date_short_end_match.span()[0]]
                subset_datestr_match = re.search(r"\d{4}\.\d{2}\.\d{2}", line_subset)

                if subset_datestr_match is None:
                    print("WARNING: Line {0}:\n{1}\n...does not contain a date string in the YYYY.MM.DD format.".format(
                        i + 1,
                        lines[i + 1]
                    ))

                else:
                    # Sanity check to make soure our logic checks out. All 3 of these should be valid matches here.
                    assert date_short_start_match is not None \
                           and date_short_end_match is not None \
                           and subset_datestr_match is not None

                    # The part before (and including) the date_short_start_comment
                    line_part_1 = line[:date_short_start_match.span()[1]]
                    # The part of the middle subset before the YYYY.MM.DD string
                    line_part_2 = line_subset[:subset_datestr_match.span()[0]]
                    # The new YYYY.MM.DD string.
                    line_part_3 = date_str
                    # The part of the middle subset after the YYYY.MM.DD string
                    line_part_4 = line_subset[subset_datestr_match.span()[1]:]
                    # The part after (and including) the date_short_end_comment
                    line_part_5 = line[date_short_end_match.span()[0]:]
                    line = line_part_1 + line_part_2 + line_part_3 + line_part_4 + line_part_5

        # Swap the line in the file with the new line we just created.
        lines_out[i] = line

    print("ORIGINAL LINES:")
    for oline in lines:
        print(oline, end="")

    print("\nNEW LINES:")
    for nline in lines_out:
        print(nline, end="")

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
