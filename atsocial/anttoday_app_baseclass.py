"""
anttoday_app_baseclass.py - A base class for making posts to various social media platforms.

Created by Mike MacFerrin
"""

import datetime
import os
import pandas
import re
import shutil


# A generate empty namespace class in which to hold attributes. Used by AntTodayAppBaseClass::df_to_object() method.
class NamespaceValues:
    """Generic class that takes a 2-column pandas dataframe, in which the first column is field names and the
    second column is field values, and converts it into an object with named attributes.
    """

    def __init__(self, df):
        for i, row in df.iterrows():
            name = row.iloc[0]
            val = row.iloc[1]
            setattr(self, name, val)


class PostInfo:
    """A simple container class in which to put variables from social media posts."""

    def __init__(self,
                 post_id: int,
                 date_covered: str = '',
                 reply_to_id: int = None,
                 timestamp: datetime.datetime = None,
                 text: str = None,
                 img1_path: str = None,
                 img1_alt: str = None,
                 img2_path: str = None,
                 img2_alt: str = None,
                 img3_path: str = None,
                 img3_alt: str = None,
                 img4_path: str = None,
                 img4_alt: str = None,
                 comments: str = None
                 ):
        self.post_id = post_id
        self.date_covered = date_covered
        self.reply_to_id = reply_to_id
        self.timestamp = timestamp
        self.text = "" if text is None else text.replace("\n", r'\n')
        self.img1 = "" if img1_path is None else img1_path
        self.img1_alt = "" if img1_alt is None else img1_alt.replace("\n", r'\n')
        self.img2 = "" if img2_path is None else img2_path
        self.img2_alt = "" if img2_alt is None else img2_alt.replace("\n", r'\n')
        self.img3 = "" if img3_path is None else img3_path
        self.img3_alt = "" if img3_alt is None else img3_alt.replace("\n", r'\n')
        self.img4 = "" if img4_path is None else img4_path
        self.img4_alt = "" if img4_alt is None else img4_alt.replace("\n", r'\n')
        self.comments = comments

    def list(self):
        """Convert the fields to a dict for easy import into pandas rows."""
        return [
            self.post_id,
            self.reply_to_id,
            self.timestamp,
            self.text,
            self.img1,
            self.img1_alt,
            self.img2,
            self.img2_alt,
            self.img3,
            self.img3_alt,
            self.img4,
            self.img4_alt,
            self.comments,
        ]

    def __str__(self):
        return str(self.list())


class AntTodayAppBaseClass:
    """A base class defining the behavior for platform-specific apps to create posts and maintain threads."""

    def __init__(self, platform_name):
        self.platform_name = platform_name
        self.username = None
        self.credentials_obj = None
        self.post_history_df = None
        self.post_history_csv_fname = None
        self.post_limit = None
        self.alt_text_limit = None
        self.text_addition = ''
        self.session = None
        self.thread_posts_cache = None
        self.top_post_id = None

    def df_to_object(self, df):
        """For a simple 2-column dataframe where the first column is an attribute name and the second is a data value,
        just convert it to a Namespace object with the attribute names as members."""
        assert len(df.columns) == 2

        # Rather than a "key: value" dataframe (which is kind of a pain to use), convert it to an object with named
        # attributes from the dataframe table.
        obj = NamespaceValues(df)

        return obj

    def populate_metadata(self):
        """Read the platform metadata file, and populate the needed fields."""
        # First, read the overall app metadata CSV.
        platform_data_csvname = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                             "..",
                                                             "data",
                                                             "platform_data.csv"))
        assert os.path.exists(platform_data_csvname)
        platform_data_df = pandas.read_csv(platform_data_csvname, comment="#").replace(pandas.NA, '')

        # Find the one entry that mathes our platform.
        platform_data_entry = platform_data_df[platform_data_df["platform_name"] == self.platform_name]
        # Make sure an entry exists for this platform.
        assert len(platform_data_entry) == 1

        platform_data_row = platform_data_entry.iloc[0]

        self.post_limit = platform_data_row.post_limit
        self.alt_text_limit = platform_data_row.alt_text_limit
        self.username = platform_data_row.username
        self.text_addition = "" if \
            (platform_data_row.text_addition is None
             or platform_data_row.text_addition == ""
             or pandas.isna(platform_data_row.text_addition)
             ) \
            else platform_data_row.text_addition.replace(r'\n', "\n")

        # Find the post history CSV in the same "data" directory as the overall platform_data file.
        post_history_csv_fname = os.path.join(os.path.dirname(platform_data_csvname),
                                              platform_data_row.post_history_file)
        assert os.path.exists(post_history_csv_fname)

        self.post_history_df = pandas.read_csv(post_history_csv_fname,
                                               comment="#",
                                               keep_default_na=False,
                                               index_col='post_id').replace(pandas.NA, '')
        self.post_history_csv_fname = post_history_csv_fname
        self.top_post_id = self.post_history_df.iloc[0].name

        # Find the credentials CSV in the "credentials" folder.
        credentials_csv_fname = os.path.join(os.path.dirname(platform_data_csvname),
                                             "..", "credentials",
                                             platform_data_row.credentials_file)
        assert os.path.exists(credentials_csv_fname)

        self.credentials_obj = self.df_to_object(pandas.read_csv(credentials_csv_fname, header=None))

        # print(self.platform_name)
        # print(self.post_history_df)
        # print(self.credentials_obj, [attr for attr in dir(self.credentials_obj) if attr[0] != "_"])

    def open_connection(self):
        """Connect to the server and get ready to post."""
        # If we haven't already logged in, do so.
        if self.credentials_obj is None:
            self.populate_metadata()
        # Make sure that worked.
        assert self.credentials_obj is not None

        self.session = self._login()
        return

    def open_and_populate(self):
        self.populate_metadata()
        self.open_connection()
        return

    def update_thread_data_file(self,
                                new_date_covered: str = None,
                                new_comment: str = None,
                                overwrite: bool = True):
        """Go through the thread using the base ID, and fill in whatever missing data is in the post_history csv to bring
        it up to speed.

        The base_id should be the post_id of the first entry in the CSV.
        """
        # Open up the post history, retreive the first post_id.
        if self.post_history_df is None:
            self.populate_metadata()

        assert self.post_history_df is not None
        post_df = self.post_history_df

        # Fetch the ID of the root post from the table.
        post_ids = post_df.index.tolist()
        first_post_id = post_ids[0]

        # Get the list of all the posts from online.
        online_post_list = self.retrieve_post_thread(first_post_id, return_as_postinfo_objects=True)

        # print(post_df)

        # Fill in the values for any line that has either incomplete data (defined if the timestamp is unfilled)
        # or no data for an entry at all (in which case, add a line).
        info_changed = False

        for post_info in online_post_list:
            matching_lines = post_df.loc[post_df.index == post_info.post_id]
            # If there is no post with this post_id, add it in new.
            if len(matching_lines) == 0:
                new_line = pandas.DataFrame(data=post_info.__dict__,
                                            index=[0]).set_index('post_id').replace(pandas.NA, '')
                # print(post_df)
                # print(post_df.columns)
                # print(new_line)
                # print(new_line.columns)
                post_df = pandas.concat([post_df, new_line])
                info_changed = True
                continue

            # If we do have a matching line, it'd better only be one. Otherwise we have repeat lines in this CSV, which
            # shouldn't be.
            assert len(matching_lines) == 1

            # If the row already has data, just move alone.
            if not (pandas.isnull(matching_lines['timestamp'].iloc[0]) or (matching_lines['timestamp'].iloc[0] == '')):
                continue

            # Otherwise, fill in this row with the data
            # post_df.set_index('post_id')
            post_newline = pandas.DataFrame(data=post_info.__dict__,
                                            index=[0]).set_index('post_id').replace(pandas.NA, '')
            post_df.update(post_newline)
            # post_df.loc[post_df['post_id'] == post_info.post_id, :] = post_info.list()
            info_changed = True

        # Just use empty strings for nan values. Just to make sure here (probably redundant but oh well.
        post_df = post_df.replace(pandas.NA, '')

        # print(post_df)
        # print(post_df.index.equals(last_post_id))

        # When we put a new post in this thread, the very last entry should have no "data_covered" field entered.
        # We provide that. Enter it here.
        if info_changed or (new_date_covered is not None) or (new_comment is not None):
            last_date_covered = post_df.iloc[len(post_df) - 1]['date_covered']
            last_post_id = post_df.index.values[-1]
            # print("LAST_POST_ID", last_post_id)
            # assert type(last_post_id) in (str, int)
            # Assign the new date covered into the post and update the dataframe with that line.
            # It will insert the dataframe in the right spot since we're using the same post_id as an index.
            if last_date_covered == "":
                # print(last_line)
                post_df.loc[post_df.index.values == last_post_id, "date_covered"] = new_date_covered
                # print(last_line)
                # post_df.update(last_line)
                info_changed = True

            # If we've added a new comment, put it here. Doesn't matter if we overwrite it.
            if new_comment is not None:
                assert type(new_comment) is str
                post_df.loc[post_df.index.values == last_post_id, "comments"] = new_comment
                info_changed = True

        # print(post_df["date_covered"])

        # print(post_df)
        # print(post_df.columns)
        # for colname in post_df.columns:
        #     print(colname, post_df[colname])

        # print(post_df)
        # print(post_df['timestamp'])

        # If the information was changed, write back out the csv.
        if info_changed and overwrite:
            # First, create a backup of the old csv.
            base, ext = os.path.splitext(self.post_history_csv_fname)
            csv_old_name = base + "_old" + ext
            if os.path.exists(csv_old_name):
                os.remove(csv_old_name)
            shutil.copyfile(self.post_history_csv_fname, csv_old_name)

            # Save it to the CSV.
            post_df.to_csv(self.post_history_csv_fname,
                           mode='w',
                           na_rep='')
            # index=False)
            print(os.path.basename(self.post_history_csv_fname), "written with {0} entries.".format(len(post_df)))
            print("(Previous {0} --> {1} as backup.)".format(os.path.basename(self.post_history_csv_fname),
                                                             os.path.basename(csv_old_name)))

        # Save it to the object parameter storing the current df. Overwrite the old one. If nothing was changed this
        # should be exactly the same.
        self.post_history_df = post_df

        return post_df

    def retrieve_post_thread(self,
                             top_post_id: str,
                             return_as_postinfo_objects: bool = True) -> list:
        """
        Retrieve a list of PostInfo objects of the entire Antarctica Today thread on this platform.

        This is a base class virtual funtion (meant to be overridden) for child classes.
        """
        raise NotImplementedError(
            "Virtual base class method " + str(self.retrieve_post_thread) + " should not be called."
                                                                            " Method should be overridden by sub-class implementation.")

    def _login(self):
        """Simple base-class virtual definition utiilized by sub-classes. Return an active session object."""
        raise NotImplementedError("Virtual base class method " + str(self._login) + " should not be called."
                                                                                    " Method should be overridden by sub-class implementation.")

    def find_latest_thread_post(self):
        """Find the latest thread post.

        First will find the latest post in the thread that came from us (not in reply to others' posts, only ours).
        """
        posts = self.retrieve_post_thread(self.top_post_id,
                                          return_as_postinfo_objects=False)
        return posts[-1]

    def post(self,
             text: str,
             date_covered: str,
             image1: str,
             image1_alt: str,
             image2: str,
             image2_alt: str,
             image3: str,
             image3_alt: str,
             image4: str,
             image4_alt: str,
             reply_to_latest: bool = True):
        """Add a post to the thread and record it into the post history."""

        # Add any needed text additions here, specified in platform_data.csv
        # These are usually just a few icons or emojis that we want to add to the post in a given particular platform.
        if not (self.text_addition is None or self.text_addition == ""):
            text = text + self.text_addition

        # Check to make sure "date_covered" has not already been covered in the database.
        post_df = self.post_history_df
        last_date_covered = max(post_df["date_covered"].tolist())
        # Both dates should be in a "YYYY.MM.DD" format. Verify this.
        assert re.search(r'\A\d{4}\.\d{2}\.\d{2}\Z', date_covered) is not None
        assert re.search(r'\A\d{4}\.\d{2}\.\d{2}\Z', last_date_covered) is not None

        # We can do a direct string comparison here. It works.
        if date_covered <= last_date_covered:
            print("Date '{0}' has already been covered on {1}. Moving along.".format(date_covered,
                                                                                     self.platform_name)
                  )
            # Return the latest post in the thread.
            return self.post_history_df.index.values[-1]


        # print("New post ({0} chars):".format(len(text)))
        # print(text)
        # FOOBAR

        # Populate the images, alt-text, text, and post. This will use the sub-class "_create_post()" method.
        response = self._create_post(
            text,
            image1,
            image1_alt,
            image2,
            image2_alt,
            image3,
            image3_alt,
            image4,
            image4_alt,
            reply_to_latest=reply_to_latest)
        # Get the record of this post from the method call above.
        # Populate the post hitory with the new post.

        # Since the thread now updated, we'll delete our previous cache so that it gets redone, and then prompt the
        # thread data to be updated.
        self.thread_posts_cache = None
        self.update_thread_data_file(new_date_covered=date_covered,
                                     overwrite=True)
        print(os.path.basename(self.post_history_csv_fname), "updated.")

        # Get the post_id of the latest post, and return it.
        return self.post_history_df.index.values[-1]

    def TEST_update_post_history_csv(self):
        df = pandas.read_csv(self.post_history_csv_fname,
                             comment="#",
                             keep_default_na=False,
                             index_col='post_id').replace(pandas.NA, '')

        print("INDEX:", df.index)
        print("COMMENTS:", df["comments"])
        df.iloc[len(df) - 1]["comments"] = "FOOBAR"
        # print(last_row)
        # last_row["comments"] = 'FOOBAR'
        # print(last_row)
        # df.update(last_row)
        print("COMMENTS_AFTER:", df["comments"])

    # def get_post_data(self,
    #                   post_id: int):
    #     """Get the status & details of a post from its ID number."""

    # THIS IS JUST AN EMPTY DEFINITION OF THE SUB-CLASS FUNCTIONT THAT SHOULD BE WRITTEN IN EACH SUB-CLASS.
    # def _create_post(self,
    #                  text: str,
    #                  image1: str,
    #                  image1_alt: str,
    #                  image2: str,
    #                  image2_alt: str,
    #                  image3: str,
    #                  image3_alt: str,
    #                  image4: str,
    #                  image4_alt: str,
    #                  reply_to_latest: bool = True) -> int:
    #     """Create a post with the necessary data, fetch the latest reply, a post to the thread.
    #
    #     Return the id of the new post."""
    #     pass
