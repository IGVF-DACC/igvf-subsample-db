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
        description="Subsamples UUIDs from IGVF/ENCODE PG Database."
    )
    parser.add_argument(
        "rule_file",
        help="Subsampling rule JSON file."
    )
    parser.add_argument(
        "-o", "--output",
        help="File path for output CSV.",
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
        default="127.0.0.1",
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

    with open(args.rule_file) as fp:
        rule = json.load(fp)

    database = Database(
        database=args.database,
        user=args.user,
        password=args.password,
        host=args.host,
        port=args.port,
    )
    profiles = Profiles(database)

    # subsample UUIDs with rule for each profile
    subsampled_uuids = profiles.subsample(rule)

    # find all linked UUIDs
    profiles.add_uuids(subsampled_uuids)
    linked_uuids = profiles.get_linked_uuids()

    with open(args.output, "w") as fp:
        fp.write("rid\n")
        fp.write("\n".join(linked_uuids))


if __name__ == "__main__":
    main()
