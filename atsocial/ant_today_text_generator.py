"""Code for creating text (including image alts) for Antarctica Today posts."""

import datetime
import os
import pandas
import re


# def ordinal_text(n):
#     # Take an integer day (e.g. 11), return an ordinal string (e.g. "11th")
#     return str(n) + ("th" if 4 <= n % 100 <= 20 else {1:"st",2:"nd",3:"rd"}.get(n % 10, "th"))

# A namespace class in which to hold attributes for Antarctica Today text values and make appropriate substitutions.
class ATTextValues:
    """Generic class that takes a 2-column pandas dataframe, in which the first column is field names and the
    second column is field values, and converts it into an object with named attributes.
    """

    def __init__(self, df, date_str_yyyy_mm_dd):
        for i, row in df.iterrows():
            name = row.iloc[0]
            val = row.iloc[1]
            setattr(self, name, val)

        self._make_text_substitutions()
        self._substitute_dates_and_seasons(date_str_yyyy_mm_dd)

    def _make_text_substitutions(self):
        """Any field this is not all caps (usually lower-case and _ characters) is a text field we'll use.
        Any fieldname that is in ALLCAPS is substituted anywhere in the other strings where [FIELDNAME] is used.
        Make those substitutions here.

        Also, substitute all r'\n' text instasnces with newlines (\n).
        """
        non_caps_attrs = []
        all_caps_attrs = []
        for attr_name in self.__dict__:
            if self._is_all_caps(attr_name):
                all_caps_attrs.append(attr_name)
            else:
                non_caps_attrs.append(attr_name)

        for attr_name in non_caps_attrs:
            # Get the text template to search through.
            attr_str = getattr(self, attr_name)
            # attr_str_orig = attr_str

            for attr_subtitution_label in all_caps_attrs:
                # Look for any instance of [FIELDNAME] in the string. If it's there, substitute the value.
                search_str = "[" + attr_subtitution_label + "]"
                # If we've found it, substitute the text.
                if attr_str.find(search_str) >= 0:
                    # Substitute the text.
                    attr_str = attr_str.replace(search_str, getattr(self, attr_subtitution_label))

            # Substitute newlines.
            attr_str = attr_str.replace(r'\n', "\n")

            # Then, re-assign the attribute to the new string with substitutions.
            # print(attr_name, attr_str_orig, "~~>", attr_str, "\n")
            setattr(self, attr_name, attr_str)

    @staticmethod
    def _is_all_caps(in_str: str) -> bool:
        """Given a string, return whether this is all-capital letters."""
        return re.search(r"\A[A-Z]+\Z", in_str) is not None

    def _substitute_dates_and_seasons(self, yyyy_mm_dd_str):
        """Replace all instances of [DATE] with a string date, and [SEASON] with a YYYY-YYYYY season string, and [YEAR]."""
        # Get the date string. Should be in "YYYY.MM.DD" format.
        dt = datetime.datetime.strptime(yyyy_mm_dd_str, "%Y.%m.%d")
        # Create a text date string, "2023.12.17" --> Sun December 17, 2023.
        date_str = dt.strftime("%a %B %d, %Y")
        # Get the season string. HERE WE ASSUME the Anarctic melt season starts 1 Oct and ends 30 April, annually.
        # First, see if the date is in the first half or the second half the season.
        mm_dd_start = (10, 1)
        mm_dd_end = (4, 30)
        mm_dd = (dt.month, dt.day)
        year = dt.year
        if mm_dd >= mm_dd_start:
            year1 = year
            year2 = year + 1
        elif mm_dd <= mm_dd_end:
            year1 = year - 1
            year2 = year
        else:
            raise ValueError(f"Year '{yyyy_mm_dd_str}' falls outside the Antarctic melt season from Oct 1 thru Apr 30.")

        season_str = f"{year1}-{year2}"

        year_str = str(datetime.datetime.today().year)

        season_search_str = "[SEASON]"
        date_search_str = "[DATE]"
        year_search_str = "[YEAR]"

        # Get all the lower-cased attributes.
        non_caps_attrs = [attrname for attrname in self.__dict__ if not self._is_all_caps(attrname)]
        for attrname in non_caps_attrs:
            attr_str = getattr(self, attrname)
            # print(attrname, attr_str, "-->")
            attr_str = attr_str.replace(season_search_str, season_str)\
                               .replace(date_search_str, date_str)\
                               .replace(year_search_str, year_str)
            # print(attr_str)
            # Assign it back into the attribute place.
            setattr(self, attrname, attr_str)

        return


def generate_text_objects(datestr):
    """Given a YYYY.MM.DD date string (the same string as the folder the images are in),
    generate the text for a post and alt-text all images in a post.

    The templates for these strings are in /data/text_templates.csv

    Returns an ATTextValues object, with the following attributes:
    .post: The main text of the post.
    .daily_melt_map_alt: Alt-text for the daily melt extent image.
    .sum_map_alt: Alt-text for the seasonal sum-of-melt-days map.
    .anomaly_map_alt: Alt-text for the seasonal anomaly-of-melt-days map.
    .line_plot_alt: Alt-text for the line plot of the season so far.
    """
    # First, find and open the text_template.csv file.
    csv_fname = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "text_templates.csv"))
    assert os.path.exists(csv_fname)

    # Read the CSV, convert it to a namespace object so we can directly get at the attributes without traversing tables.
    df = pandas.read_csv(csv_fname, comment="#", names=["name", "value"])
    # For some stupid reason (I'm too lazy to debug with Pandas right now), the comment line is being read in as a
    # data row despite starting with "#". Filter out comment lines specifically here.
    df = df[~df.name.str.startswith("#")]

    # Create the attribute object and make all the correct substitutions.
    text_obj = ATTextValues(df, datestr)
    # The text fields we should reference are:
    # - post
    # - daily_melt_map_alt
    # - sum_map_alt
    # - anomaly_map_alt
    # - line_plot_alt
    return text_obj


if __name__ == "__main__":
    print(generate_text_objects("2023.12.16").__dict__)
