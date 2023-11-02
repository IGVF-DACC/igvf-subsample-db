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
    )
    parser.add_argument(
        "-U", "--user",
        help="PG username.",
        default="postgres",
    )
    parser.add_argument(
        "-p", "--port",
        help="PG port.",
        default=5432,
    )
    parser.add_argument(
        "-H", "--host",
        help="PG hostname.",
    )
    parser.add_argument(
        "-P", "--password",
        help="PG password.",
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Print debug messages to stderr.'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    database = Database(
        database=args.database,
        user=args.user,
        password=args.password,
        host=args.host,
        port=args.port,
    )
    profiles = Profiles(database)

    template_rule = profiles.create_template_rule()

    # some users accounts are used for running services for a server
    # so we keep ALL users
    template_rule["user"] = [
        {
            "subsampling_min": 100000000,
            "subsampling_rate": 1e-05,
        }
    ]

    with open(args.output, "w") as fp:
        fp.write(json.dumps(template_rule, indent=4))


if __name__ == "__main__":
    main()
