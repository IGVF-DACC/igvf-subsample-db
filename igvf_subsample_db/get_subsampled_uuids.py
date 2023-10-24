#!/usr/bin/env python3
import argparse
import json
import logging

from igvf_subsample_db.profiles import Profiles
from igvf_subsample_db.db import Database


logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="IGVF/ENCODE UUID Subsampler."
    )
    parser.add_argument(
        "rule_file",
        help="Subsampling rule JSON file."
    )
    parser.add_argument(
        "-o", "--output-prefix",
        help="File path prefix for output CSV.",
        required=True
    )
    parser.add_argument(
        "-d", "--database",
        help="Use encoded for ENCODE, igvfd for IGVF.",
        required=True,
        choices=["encoded", "igvfd"],
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Print debug messages to stderr.'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    with open(args.rule_file) as fp:
        rule = json.load(fp)

    database = Database("encoded")
    profiles = Profiles(database)

    # subsample UUIDs with rule for each profile
    subsampled_uuids = profiles.subsample(rule)

    with open(args.output_prefix + ".subsampled.csv", "w") as fp:
        fp.write("rid\n")
        fp.write("\n".join(subsampled_uuids))

    # find all linked UUIDs
    profiles.add_uuids(subsampled_uuids)
    linked_uuids = profiles.get_linked_uuids()

    with open(args.output_prefix + ".subsampled.linked.csv", "w") as fp:
        fp.write("rid\n")
        fp.write("\n".join(linked_uuids))


if __name__ == "__main__":
    main()
