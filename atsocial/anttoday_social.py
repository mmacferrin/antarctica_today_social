"""
anttoday_social.py - A class for making posts to various social media platforms.
Currently supporting Mastodon & BlueSky (AT-proto). Not yet supporting Threads and currently choosing to not support Twitter.

Created by Mike MacFerrin
"""
import os

import ant_today_text_generator
import atproto_social
import git_image_upload
import mastodon_social
import update_antarctica_today


###############################################################################################################
# Note: To schedule this for daily auto-run, I set it up using the auto-scheduler on my (Ubuntu) workstation.
# I used the "cron" utility, described here: https://askubuntu.com/questions/1200232/task-scheduler-in-ubuntu
# You will probably want to look up the way to do it best in whatever environment you're running your app from.
###############################################################################################################


class AntTodaySocialApp:
    def __init__(self):
        self.apps = [atproto_social.AntTodayAppATProto(),
                     mastodon_social.AntTodayAppMastodon()]
        # self.apps = [atproto_social.AntTodayAppATProto()] # Un-comment to only work in BlueSky (ATProto)
        # self.apps = [mastodon_social.AntTodayAppMastodon()] # Un-comment to only work in Mastodon.

    def populate_and_connect(self):
        """Open and populate all the needed platform classes."""
        for app in self.apps:
            app.open_and_populate()

    def create_new_post(self) -> list:
        """Update Antarctica Today data and images, generate new text, and post on each social media platform."""

        # 1. Use "update_antarctica_today.py" to Update the data. Get the info of this data.

        # Fetch the date covered by this post.
        # Look in update_antarctica_today.py::AntarcticaTodayImages class definition for the namespaces here.
        at_update_object = update_antarctica_today.run_update_data()
        date_covered = os.path.split(at_update_object.dirname)[-1]

        text_fields = ant_today_text_generator.generate_text_objects(date_covered)
        # - post
        # - daily_melt_map_alt
        # - sum_map_alt
        # - anomaly_map_alt
        # - line_plot_alt

        # Post in each of the sub-apps.
        responses = [None] * len(self.apps)
        for i, app in enumerate(self.apps):
            try:
                post_id = app.post(text_fields.post,
                                   date_covered=date_covered,
                                   image1=at_update_object.daily_melt_map,
                                   image1_alt=text_fields.daily_melt_map_alt,
                                   image2=at_update_object.sum_map,
                                   image2_alt=text_fields.sum_map_alt,
                                   image3=at_update_object.anomaly_map,
                                   image3_alt=text_fields.anomaly_map_alt,
                                   image4=at_update_object.line_plot,
                                   image4_alt=text_fields.line_plot_alt,
                                   reply_to_latest=True)
                responses[i] = post_id
            except Exception as e:
                responses[i] = e

        # Upload the new images to the git repository. (This will exit out if the git is alredy current.)
        atgit = git_image_upload.ATGit()
        atgit.upload_images(at_update_object, also_update_readme=True)

        return responses


def new_post_on_all_platforms():
    atoday = AntTodaySocialApp()
    atoday.populate_and_connect()
    responses = atoday.create_new_post()
    return responses


if __name__ == "__main__":
    new_post_on_all_platforms()
