#!/usr/bin/env python3
import argparse
import logging

from igvf_subsample_db.profiles import Profiles
from igvf_subsample_db.db import Database


logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Subsamples PG Database of IGVF/ENCODE."
    )
    parser.add_argument(
        "uuids_csv",
        help="UUIDs CSV file (header 'rid' required)."
    )
    parser.add_argument(
        "-d", "--database",
        help="Database name. Use encoded for ENCODE, igvfd for IGVF.",
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

    profiles.subsample_pg(args.uuids_csv)


if __name__ == "__main__":
    main()
