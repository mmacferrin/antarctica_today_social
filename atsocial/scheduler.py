import argparse
import time

import anttoday_social


def define_and_parse_args():
    parser = argparse.ArgumentParser(
        description="Run the Antartica Today app repeatedly until it succeeds for all apps.")
    parser.add_argument("interval")