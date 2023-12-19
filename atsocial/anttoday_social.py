"""
anttoday_social.py - A class for making posts to various social media platforms.
Currently supporting Mastodon & BlueSky (AT-proto). Not yet supporting Threads and currently choosing to not support Twitter.

Created by Mike MacFerrin
"""
import os

import ant_today_text_generator
import atproto_social
import mastodon_social
import update_antarctica_today


class AntTodaySocialApp:
    def __init__(self):
        # TODO: Uncomment this when we want to enable the Mastodn app too.
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

        # Generate each of these.
        #      text: str,
        #      image1: str,
        #      image1_alt: str,
        #      image2: str,
        #      image2_alt: str,
        #      image3: str,
        #      image3_alt: str,
        #      image4: str,
        #      image4_alt: str,
        #      reply_to_latest: bool = True):
        # """Add a post to the thread and record it into the post history for all platforms included."""

        # Fetch the date covered by this post.
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

        return responses

    # def post_latest_data(self):
    #     # First, run the code to update the data in the directories.
    #     self.update_ant_today_data()
    #
    # def update_ant_today_data(self):
    #     """Run the Antarctica_Today code to get data from NSIDC and create new figures."""
    #     return_object = update_antarctica_today.run_update_data()
    #     # print(return_object)
    #     # print(return_object.__dict__)
    #     return return_object


def new_post_on_all_platforms():
    atoday = AntTodaySocialApp()
    atoday.populate_and_connect()
    responses = atoday.create_new_post()
    return responses


if __name__ == "__main__":
    new_post_on_all_platforms()

    # atoday.post(
    #     "Antarctica Today test post: Antarctic surface melt extent for 2023.12.15, as detected from passive microwave"
    #     " measurements. This is just a test, only a test.",
    #     image1="/home/mmacferrin/git/Antarctica_Today/plots/daily_plots_gathered/2023.12.14/R1_2023.12.14_daily.png",
    #     image1_alt="Daily surface melt extent for 15 Dec 2023.",
    #     image2="/home/mmacferrin/git/Antarctica_Today/plots/daily_plots_gathered/2023.12.14/R0_2023-2024_2023.12.14_sum.png",
    #     image2_alt="Sum of melt days for the 2023-24 melt season, through 14 Dec 2023.",
    #     image3="/home/mmacferrin/git/Antarctica_Today/plots/daily_plots_gathered/2023.12.14/R0_2023-2024_2023.12.14_anomaly.png",
    #     image3_alt="Anomaly of the sum of melt days for the 2023-24 melt season, through 14 Dec 2023, compared to the"
    #                " 1990-2020 historical averages.",
    #     image4="/home/mmacferrin/git/Antarctica_Today/plots/daily_plots_gathered/2023.12.14/R0_2023-2024_2023.12.14_gap_filled.png",
    #     image4_alt="Daily timeline line-plot of surface melt extent for each day of the 2023-24 Antartic melt season, through"
    #                " 14 Dec 2023.",
    #     reply_to_latest=True)
