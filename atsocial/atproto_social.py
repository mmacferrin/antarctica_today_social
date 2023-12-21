import argparse
import atproto
import atproto.utils
import re

import anttoday_app_baseclass


class AntTodayAppATProto(anttoday_app_baseclass.AntTodayAppBaseClass):

    def __init__(self):
        super(AntTodayAppATProto, self).__init__("bluesky")

    def _login(self):
        # This should already be populated.
        creds_obj = self.credentials_obj
        assert creds_obj is not None
        assert hasattr(creds_obj, "username")
        assert hasattr(creds_obj, "app_password")

        client = atproto.Client()
        client.login(creds_obj.username, creds_obj.app_password)

        return client

    def get_post_data(self,
                      post_id: str):
        """Get the status & details of a post from its ID number."""
        search_results = self.session.app.bsky.feed.get_post_thread({"uri": post_id,
                                                                     "depth": 1,
                                                                     "parent_height": 0})
        return search_results

    def retrieve_post_thread(self,
                             top_post_id: str,
                             return_as_postinfo_objects: bool = True) -> list:
        """Return a list of post attribute data of all self-response replies in a thread to the original post."""
        current_post_id = top_post_id

        # If we've already retrieved the whole damned thread this session, don't both repeating, just fetch it.
        if self.thread_posts_cache is not None:
            assert self.thread_posts_cache[0].uri == top_post_id
            posts = self.thread_posts_cache

        else:
            still_more_replies = True

            posts = []

            i = 1
            while still_more_replies:
                # Do a thread search on this post. This will give us the post information plus references to replies.
                search_results = self.session.app.bsky.feed.get_post_thread({"uri": current_post_id,
                                                                             "depth": 1,
                                                                             "parent_height": 0})

                post = search_results.thread.post
                # print(i, post.uri, "by", post.author.handle + ":")
                # print(post.record.created_at)
                # if post.record.reply is not None:
                #     print("in response to:", post.record.reply.parent.uri)
                # print(post.record.text)
                # if post.embed is None:
                #     print("No images.")
                # else:
                #     print(len(post.embed.images), "images:")
                #     for j, image in enumerate(post.embed.images):
                #         print("  {0}: {1}h {2}w {3} '{4}'".format(j + 1,
                #                                               image.aspect_ratio.height,
                #                                               image.aspect_ratio.width,
                #                                               image.fullsize,
                #                                               image.alt))
                #
                # print()
                posts.append(post)

                # If a reply is one that we authored, continue down that path. IMPORTANT: If we reply more than once to a
                # single post, it will be important for us to put which post we want to follow as an entry in the post_history csv.
                # Otherwise we could chase down the wrong reply branch.
                # print(self.username)
                # print(search_results.thread.replies[0].post.author.handle)
                replies_from_us = [reply.post for reply in search_results.thread.replies if
                                   reply.post.author.handle == self.username]

                if len(replies_from_us) == 0:
                    still_more_replies = False
                    continue

                # Find the reply, from us, that has the most replies after it. This is an imperfect measure but good for now.
                # This should be unneeded logic since I don't plan to create multiple forks in the same thread with my own
                # responses. I plan to just reply directly in the thread linearly.
                most_populated_reply = replies_from_us[0]
                for reply in replies_from_us[1:]:
                    if most_populated_reply.reply_count < reply.reply_count:
                        most_populated_reply = reply

                current_post_id = most_populated_reply.uri
                still_more_replies = True

                i += 1

            # Save in the cache for later.
            self.thread_posts_cache = posts

        if return_as_postinfo_objects:
            # Turn all the posts into PostInfo objects.
            postinfo_objects = [None] * len(posts)
            for i, post in enumerate(posts):
                post = posts[i]
                num_images = 0 if (post.embed is None or
                                   not hasattr(post.embed, "images") or
                                   len(post.embed.images) == 0)\
                             else len(post.embed.images)
                post_obj = anttoday_app_baseclass.PostInfo(
                    post_id=post.uri,
                    reply_to_id=None if post.record.reply is None else post.record.reply.parent.uri,
                    timestamp=post.record.created_at,
                    text=post.record.text,
                    img1_path=post.embed.images[0].fullsize if (num_images >= 1) else None,
                    img1_alt=post.embed.images[0].alt if (num_images >= 1) else None,
                    img2_path=post.embed.images[1].fullsize if (num_images >= 2) else None,
                    img2_alt=post.embed.images[1].alt if (num_images >= 2) else None,
                    img3_path=post.embed.images[2].fullsize if (num_images >= 3) else None,
                    img3_alt=post.embed.images[2].alt if (num_images >= 3) else None,
                    img4_path=post.embed.images[3].fullsize if (num_images >= 4) else None,
                    img4_alt=post.embed.images[3].alt if (num_images >= 4) else None,
                    comments=None,
                )
                postinfo_objects[i] = post_obj

            return postinfo_objects

        else:
            # Otherwise, just return as the atproto post class objects.
            return posts

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
                     reply_to_latest: bool = True):
        """Create a post with the necessary data, fetch the latest reply, a post to the thread.

        Return the id of the new post."""
        # Get the info of the latest post we shoudl be replying to.
        if reply_to_latest:
            last_post_obj = self.find_latest_thread_post()

            # print("last_post_obj", type(last_post_obj))
            # print(last_post_obj)
            # text = "  \n\n".join(["{0}: {1}".format(attr, getattr(last_post_obj, attr)) for attr in dir(last_post_obj) if attr[0] != "_"])
            # print(text)
            # parent_loc = text.lower().find("replyref=")
            # print("\n\n===================\nreplyref= at:", parent_loc, "\n", text[max(0, parent_loc - 3000) : parent_loc + 150])

            reply_obj = last_post_obj.record.reply
            # Except, the last post in that thread was in response to the one before it. We want our post to be in
            # response to the last post, so change the data of the 'parent' to point to the last post instead.
            if reply_obj is None:
                # If the last post was the first post of the thread, it has no "record.reply" object in it. So create
                # one pointing to the top post.
                # I'm having trouble coding up a valid ReplyRef object here by scratch because the atproto API is a PITA.
                # So I'm just going to grab a one from online and change the parameters as needed.
                # Just using one of my previous reply posts in a longer random thread, url here:
                # https://bsky.app/profile/icesheetmike.bsky.social/post/3kgrpb7qb562h
                # And then changing the reply_obj... .uri and .cid fields to make atproto happy with it..
                random_reply_post = self.get_post_data(post_id="at://did:plc:iqcyflkt2gun674dnbssobt6/app.bsky.feed.post/3kgrpb7qb562h")

                # This is where a valid ReplyRef object sits in that return object.
                reply_obj = random_reply_post.thread.post.record.reply
                # Change it to point to reply to the post I want it to reply to.
                reply_obj.parent.uri = last_post_obj.uri
                reply_obj.parent.cid = last_post_obj.cid

                # This code is still broken, don't have the energy to debug. Why does atproto make this a royal PITA.
                # reply_obj = last_post_obj
                    # (parent=last_post_obj,
                    #                                                    root=last_post_obj))
                # reply_obj.parent = last_post_obj
            else:
                reply_obj.parent.uri = last_post_obj.uri
                reply_obj.parent.cid = last_post_obj.cid

        else:
            # last_post_obj = None
            reply_obj = None

        # print("LAST POST OBJ:")
        # print(last_post_obj)
        # text = "  \n\n".join(["{0}: {1}".format(attr, getattr(last_post_obj, attr)) for attr in dir(last_post_obj) if attr[0] != "_"])
        # print(text)
        # reply_ref_loc = text.lower().find("replyref")
        # print("\n\n===================\nREPLY_REF AT:", reply_ref_loc, "\n", text[reply_ref_loc - 3000 : reply_ref_loc + 150])

        image_objs = []
        for (img_fn, img_alt) in [(image1, image1_alt),
                                  (image2, image2_alt),
                                  (image3, image3_alt),
                                  (image4, image4_alt)]:
            if img_fn is not None:
                # Look at https://github.com/MarshalX/atproto/blob/main/atproto/xrpc_client/client/client.py reference.
                # Use the code from "send_image" to make a post that sends multiple images. Same fuckin' code, they
                # just didn't finish it. You can.
                img_data = open(img_fn, 'rb').read()
                upload = self.session.com.atproto.repo.upload_blob(img_data)
                image_obj = atproto.models.AppBskyEmbedImages.Image(alt=img_alt, image=upload.blob)
                image_objs.append(image_obj)

        # Build embed objects for images.
        if len(image_objs) > 0:
            embeds = atproto.models.AppBskyEmbedImages.Main(images=image_objs)
        else:
            embeds = None

        response = self.session.send_post(text=text,
                                          reply_to=reply_obj,
                                          embed=embeds)

        # print("RESPONSE:")
        # print(response)
        # print("RESPONSE FIELDS:")
        # print(
        #     "  \n".join(["{0}: {1}".format(attr, getattr(response, attr)) for attr in dir(response) if attr[0] != "_"]))

        # Rather than return the whole response object, just get the URI of the reponse post we just made.
        #  That's all we need to return.
        return response.uri


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
        print("ERROR: The argument -date must be in a YYYY.MM.DD format, which '{0}' is not. Exiting.".format(args.date))

    app = AntTodayAppATProto()
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

    # app.populate_metadata()
    # app.TEST_update_post_history_csv()

    # data = app.get_post_data(r"at://did:plc:iqcyflkt2gun674dnbssobt6/app.bsky.feed.post/3kgm4ufvnsm2b")
    # thread_list = app.retrieve_post_thread(r"at://did:plc:iqcyflkt2gun674dnbssobt6/app.bsky.feed.post/3kgm4ufvnsm2b")
    # print(thread_list[-1].__dict__)
    #
    # print(len(thread_list), "posts in thread.")
    # for post in thread_list:
    #     print(post)
