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
        description="Create a template rule JSON."
    )
    parser.add_argument(
        "-o", "--output",
        help="Subsampling rule JSON file.",
        required=True
    )
    parser.add_argument(
        "-d", "--database",
        help="Use encoded for ENCODE, igvfd for IGVF.",
        required=True,
        choices=["encoded", "igvfd", "test_encoded", "test_igvfd"],
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Print debug messages to stderr.'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    database = Database(args.database)
    profiles = Profiles(database)

    rule_template = profiles.create_rule_template()

    with open(args.output, "w") as fp:
        fp.write(json.dumps(rule_template, indent=4))


if __name__ == "__main__":
    main()
