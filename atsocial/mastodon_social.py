import argparse
from mastodon import Mastodon
import os

import anttoday_app_baseclass


class AntTodayAppMastodon(anttoday_app_baseclass.AntTodayAppBaseClass):

    def __init__(self):
        super(AntTodayAppMastodon, self).__init__("mastodon")

    def _login(self):
        # This should already be populated.
        creds_obj = self.credentials_obj
        assert creds_obj is not None
        assert hasattr(creds_obj, "client_id")
        assert hasattr(creds_obj, "client_secret")
        assert hasattr(creds_obj, "access_token")
        assert hasattr(creds_obj, "api_base_url")

        session = Mastodon(
            client_id=creds_obj.client_id,
            client_secret=creds_obj.client_secret,
            access_token=creds_obj.access_token,
            api_base_url=creds_obj.api_base_url,
        )

        # print("Mastodon session:", session)
        # DO this only if you want to see all the possible dir function calls available.
        # print("\n".join([attrname for attrname in dir(session) if attrname[0] != "_"]))
        # base_post_id = 111585893215986462
        # context = session.status_context(base_post_id)
        # status = session.status(base_post_id)
        # print("Status:", status)
        # print("Context:", context)
        # print("Welcome to Mastodon,", context.keys, context.keys(), dir(context))
        return session

    def retrieve_post_thread(self,
                             top_post_id: str,
                             return_as_postinfo_objects: bool = True) -> list:
        """Return a list of post attribute data of all self-response replies in a thread to the original post."""
        # First, get the top post.
        top_post_id = int(top_post_id)
        top_post = self.session.status(top_post_id)
        top_context = self.session.status_context(top_post_id)

        posts_list = [top_post]

        descendants = top_context.descendants

        if len(descendants) == 0:
            assert hasattr(top_post, "id")
            if return_as_postinfo_objects:
                num_images = len(top_post.media_attachments)
                post_obj = anttoday_app_baseclass.PostInfo(
                    post_id=top_post.id,
                    reply_to_id='' if top_post.in_reply_to_id is None else post.in_reply_to_id,
                    timestamp=top_post.created_at,
                    text=top_post.content,
                    img1_path=top_post.media_attachments[0].url if (num_images >= 1) else None,
                    img1_alt=top_post.media_attachments[0].description if (num_images >= 1) else None,
                    img2_path=top_post.media_attachments[1].url if (num_images >= 2) else None,
                    img2_alt=top_post.media_attachments[1].description if (num_images >= 2) else None,
                    img3_path=top_post.media_attachments[2].url if (num_images >= 3) else None,
                    img3_alt=top_post.media_attachments[2].description if (num_images >= 3) else None,
                    img4_path=top_post.media_attachments[3].url if (num_images >= 4) else None,
                    img4_alt=top_post.media_attachments[3].description if (num_images >= 4) else None,
                    comments=None,
                )
                return [post_obj]

            else:
                return posts_list
        else:
            desc_from_original_user = [desc for desc in descendants if
                                       (desc.account.username == top_post.account.username) and
                                       (desc.in_reply_to_account_id == top_post.account.id)]
            posts_list = posts_list + desc_from_original_user

        # Make sure that all these posts were in replies only to myself
        posts_sorted = sorted(posts_list, key=lambda x: x.id)

        # Run through IN ORDER, and make sure that each one descended from the previous one. Skip any ones that aren't.
        prev_post = posts_sorted[0]
        posts_sorted_linear = [posts_sorted[0]]
        for i in range(1, len(posts_sorted)):
            this_post = posts_sorted[i]
            if (this_post.in_reply_to_id == prev_post.id) and \
                    (this_post.in_reply_to_account_id == prev_post.account.id):
                posts_sorted_linear.append(this_post)
                prev_post = this_post
            else:
                continue

        # print(len(posts_sorted_linear), "posts in linear thread by '{0}'.".format(posts_sorted_linear[0].account.username))

        if return_as_postinfo_objects:
            # Turn all the posts into PostInfo objects.
            postinfo_objects = [None] * len(posts_sorted_linear)
            for i, post in enumerate(posts_sorted_linear):
                num_images = len(post.media_attachments)
                post_obj = anttoday_app_baseclass.PostInfo(
                    post_id=post.id,
                    reply_to_id='' if post.in_reply_to_id is None else post.in_reply_to_id,
                    timestamp=post.created_at,
                    text=post.content,
                    img1_path=post.media_attachments[0].url if (num_images >= 1) else None,
                    img1_alt=post.media_attachments[0].description if (num_images >= 1) else None,
                    img2_path=post.media_attachments[1].url if (num_images >= 2) else None,
                    img2_alt=post.media_attachments[1].description if (num_images >= 2) else None,
                    img3_path=post.media_attachments[2].url if (num_images >= 3) else None,
                    img3_alt=post.media_attachments[2].description if (num_images >= 3) else None,
                    img4_path=post.media_attachments[3].url if (num_images >= 4) else None,
                    img4_alt=post.media_attachments[3].description if (num_images >= 4) else None,
                    comments=None,
                )
                postinfo_objects[i] = post_obj

            return postinfo_objects

        else:
            # Otherwise, just return as the atproto post class objects.
            return posts_sorted_linear

    def get_post_data(self,
                      post_id: str):
        """Get the status & details of a post from its ID number."""
        return self.session.status(post_id)

    def _create_post(self,
                     text: str,
                     image1: str,
                     image1_alt: str,
                     image2: str,
                     image2_alt: str,
                     image3: str,
                     image3_alt: str,
                     image4: str,
                     image4_alt: str,
                     reply_to_latest: bool = True) -> int:
        """Create a post with the necessary data, fetch the latest reply, a post to the thread.

        Return the id of the new post."""
        if reply_to_latest:
            last_post = self.find_latest_thread_post()
        else:
            last_post = None

        # Gather all the images.
        media_to_include = []
        for (img_name, img_desc) in zip([image1, image2, image3, image4],
                                        [image1_alt, image2_alt, image3_alt, image4_alt]):
            if img_name:
                assert os.path.exists(img_name)
                media = self.session.media_post(img_name,
                                                description=img_desc)
                media_to_include.append(media)

        new_post = self.session.status_post(text,
                                            in_reply_to_id=last_post,
                                            media_ids=None if (len(media_to_include) == 0) else media_to_include,
                                            visibility=last_post.visibility)

        return new_post.id

    def TEST_post(self,
                  text="Test post #3.",
                  img1="/home/mmacferrin/git/Antarctica_Today/plots/daily_plots_gathered/2023.12.16/R0_2023-2024_2023.12.16_sum.png",
                  alt1="TEST IMAGE 1"):

        media = self.session.media_post(img1, description=alt1)
        response = self.session.status_post(text,
                                            in_reply_to_id=111600000908489865,
                                            media_ids=[media],
                                            visibility="public")
        print(response)


def define_and_parse_args():
    parser = argparse.ArgumentParser(description="Class descrtipon for the ATProto (BlueSky) app implementation. "
                                                 "Run this independently to update the post database (optional but sometimes nice if you've added other posts.")

    parser.add_argument("-date", "-d", type=str, default="",
                        help="A date (in YYYY.MM.DD format) to add to the latest post in the thread database. This "
                             "is usually auto-generated when creating a post but you can add it here if it wasn't. "
                             "If the last post in the database doesn't have a date_covered value, it'll be added there.")
    parser.add_argument("-comment", "-c", type=str, default="",
                        help="Add a comment into the 'comments' field in the last post. These comments are not seen "
                             "with the posts, they are simply for our own benefit.")

    return parser.parse_args()


if __name__ == "__main__":

    args = define_and_parse_args()
    # The date should either be a blank string, or in the YYYY.MM.DD format. If neither, complain and exit.
    if args.date != "" and re.search(r"\A\d{4}\.\d{2}\.\d{2}\Z", args.date) is None:
        print(
            "ERROR: The argument -date must be in a YYYY.MM.DD format, which '{0}' is not. Exiting.".format(args.date))

    app = AntTodayAppMastodon()

    app.open_and_populate()
    df = app.update_thread_data_file(new_date_covered=None if (args.date == "") else args.date,
                                     new_comment=None if (args.comment == "") else args.comment)

    print("Last post info:")
    colnames = list(df.columns)
    print(df.index.name + ":")
    print("   ", df.index.values[-1], '\n')
    for cname, field in zip(colnames, df.iloc[-1].tolist()):
        print(cname + ":")
        if type(field) is str:
            print("   ", field.replace(r'\n', '\n'))
        else:
            print("   ", field)
        print()
