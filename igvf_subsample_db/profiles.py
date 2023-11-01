import logging
import math
import os
import random
from collections import defaultdict


logger = logging.getLogger(__name__)


SUBSAMPLING_RANDOM_SEED = 17
UUIDS_PER_LOG = 10000
TEMPLATE_RULE = {
    "subsampling_min": 1,
    "subsampling_rate": 1e-05,
}


class Profiles:
    def __init__(self, database):
        """
        Member variables:
            self.links:
                A dict of {source_uuid: [target_uuids...]}
            self.uuid_to_profile:
                A dict of {uuid: profile_name}
            self.profile_names:
                A set of profile names
            self._linked_uuids:
                A set of all UUIDs that linked within them
                Use self.add_uuid(uuid) to recursively add linked UUIDs
        """
        self.database = database

        logger.info("Loading links from DB...")
        self.links = defaultdict(set)
        for source_uuid, rel, target_uuid in self.database.fetchall(
            "SELECT * FROM links"
        ):
            self.links[source_uuid].add(target_uuid)

        logger.info("Loading resources from DB...")
        self.uuid_to_profile = {}
        for uuid, profile_name in self.database.fetchall(
            "SELECT * FROM resources"
        ):
            self.uuid_to_profile[uuid] = profile_name

        logger.info("Loading distinct profiles from DB...")
        self.profile_names = set()

        for profile_name, in self.database.fetchall(
            "SELECT DISTINCT(item_type) FROM resources"
        ):
            self.profile_names.add(profile_name)

        self._linked_uuids = set()

    def create_template_rule(self):
        """
        Returns a template rule JSON.
        """
        result = {}
        for profile_name in self.profile_names:
            result[profile_name] = [TEMPLATE_RULE.copy()]

        return result

    def subsample(self, rule):
        """
        Returns a set of UUIDs

        Args:
            rule:
                A dict of {profile_name: [rules...]}
                profile_name should be in a snakecase format.

                Example:
                {
                    "experiment": [
                        {
                            "subsampling_rate": 0.0,
                            "subsampling_min": 1,
                            "subsampling_cond": {
                                "assay_term_name": "ChIP-seq"
                            }
                        },
                        {
                            "subsampling_rate": 0.0,
                            "subsampling_min": 5,
                            "subsampling_cond": {
                                "assay_term_name": "ATAC-seq"
                            }
                        }
                    ]
                }
        """
        # result dict
        subsampled_uuids = set()

        for profile_name in self.profile_names:
            if profile_name not in rule:
                logger.warning(
                    f"Could not find subsampling rule for profile {profile_name}."
                )
                continue

            for rule_elem in rule[profile_name]:
                # reset random seed for each rule element
                random.seed(SUBSAMPLING_RANDOM_SEED)

                subsampling_rate = rule_elem.get(
                    "subsampling_rate", 0.0
                )
                subsampling_min = rule_elem.get(
                    "subsampling_min", 1
                )
                subsampling_cond = rule_elem.get(
                    "subsampling_cond"
                )

                # make SQL string for subsampling condition
                # e.g. AND properties->>'assay_term_name'='ChIP-seq'

                if subsampling_cond:
                    cond_list = [""]
                    for prop, val in subsampling_cond.items():
                        # escape single quote for SQL WHERE clause
                        val = val.replace("'", "''")
                        cond_list.append(f"properties->>'{prop}'='{val}'")

                    cond_sql = " AND ".join(cond_list)
                else:
                    cond_sql = ""

                # old query used for ENCODE
                # query = f"SELECT rid FROM object WHERE item_type='{profile_name}' {cond_sql}"

                # unlike ENCODE, IGVF doesn't have a view 'object'
                # so here we join two tables with rid using SELECT DISTINCT ON
                # to get top 1 row of 'propsheets' table grouped by rid
                query = f"""
                        WITH props AS (
                            SELECT DISTINCT ON (rid) rid, properties
                            FROM propsheets
                        )
                        SELECT resources.rid
                        FROM resources
                        LEFT JOIN props ON props.rid = resources.rid
                        WHERE item_type='{profile_name}' {cond_sql}
                        """

                logger.info(
                    f"Subsampling for profile {profile_name} with "
                    f"cond {subsampling_cond}, Query: {query}"
                )

                uuids = []
                for uuid, in self.database.fetchall(query):
                    uuids.append(uuid)

                if not uuids:
                    logger.warning(
                        f"Found 0 objects matching condition: {subsampling_cond}"
                    )
                    continue

                num_subsampled = max(
                    math.floor(subsampling_rate * len(uuids)),
                    subsampling_min
                )
                if num_subsampled:
                    subsampled = set(random.choices(uuids, k=num_subsampled))
                    logger.debug(f"\t{subsampled}")
                    subsampled_uuids.update(subsampled)

        return subsampled_uuids

    def add_uuids(self, uuids):
        for uuid in uuids:
            self.add_uuid(uuid)

    def add_uuid(self, uuid, depth=0, parent_uuids=()):
        """
        Recursively add UUIDs by traversing a tree search in a top-down fashion.
        i.e. source -> target in links table.
        """
        if uuid in self._linked_uuids:
            return

        if uuid in parent_uuids:
            logger.debug(
                f"Cyclic ref found. {depth}: {uuid}, {self.uuid_to_profile[uuid]}"
            )
            return

        if depth > 300:
            logger.debug(
                f"Search tree is too deep. {depth}: {uuid}, {self.uuid_to_profile[uuid]}"
            )

        self._linked_uuids.add(uuid)

        parent_uuids += (uuid,)
        depth += 1

        if len(self._linked_uuids) % UUIDS_PER_LOG == 0:
            logger.info(
                f"Number of all linked UUIDs = {len(self._linked_uuids)} so far."
            )

        for linked_uuid in self.links[uuid]:
            self.add_uuid(
                linked_uuid, depth=depth, parent_uuids=parent_uuids
            )

    def get_linked_uuids(self):
        return self._linked_uuids

    def subsample_pg(self, csv_file):
        """
        Subsamples PG database down to include uuids only in csv_file.
        """
        csv_file = os.path.abspath(csv_file)

        logger.info("Transaction 1: Create a temp table and insert UUIDs from CSV.")

        with self.database.conn:
            with self.database.conn.cursor() as cur:

                logger.info("Creating a temporary UUIDs table...")
                cur.execute(
                    """
                    CREATE TABLE subsampled_rids(
                      id SERIAL PRIMARY KEY,
                      profile_name VARCHAR(50),
                      rid UUID,
                      UNIQUE(rid)
                    );
                    """
                )

                logger.info("Inserting UUIDs into temp table...")
                # use copy_expert() to make it work with remote server
                with open(csv_file) as fp:
                    cur.copy_expert(
                        """
                        COPY subsampled_rids(rid)
                        FROM STDIN WITH HEADER CSV;
                        """,
                        fp
                    )

        logger.info("Transaction 2: Alter tables.")

        with self.database.conn:
            with self.database.conn.cursor() as cur:

                logger.info("Dropping constraints of tables...")

                logger.debug("Dropping constraint of current_propsheets")
                cur.execute(
                    """
                    ALTER TABLE current_propsheets
                      DROP CONSTRAINT "current_propsheets_rid_fkey";
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE current_propsheets
                      DROP CONSTRAINT "current_propsheets_sid_fkey";
                    """
                )

                logger.debug("Dropping constraint of keys...")
                cur.execute(
                    """
                    ALTER TABLE keys
                      DROP CONSTRAINT "keys_rid_fkey";
                    """
                )

                logger.debug("Dropping constraint of links...")
                cur.execute(
                    """
                    ALTER TABLE links
                      DROP CONSTRAINT "links_source_fkey";
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE links
                      DROP CONSTRAINT "links_target_fkey";
                    """
                )

                logger.debug("Dropping constraint of propsheets...")
                cur.execute(
                    """
                    ALTER TABLE propsheets
                      DROP CONSTRAINT "fk_property_sheets_rid_name";
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE propsheets
                      DROP CONSTRAINT "propsheets_rid_fkey";
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE propsheets
                      DROP CONSTRAINT "propsheets_tid_fkey";
                    """
                )

                logger.info("Deleting rows from tables...")

                logger.debug("Deleting rows from resources...")
                cur.execute(
                    """
                    DELETE FROM resources src
                    WHERE NOT EXISTS (
                       SELECT FROM subsampled_rids sub
                       WHERE  sub.rid = src.rid
                    );
                    """
                )

                logger.debug("Deleting rows from keys...")
                cur.execute(
                    """
                    DELETE FROM keys src
                    WHERE NOT EXISTS (
                       SELECT FROM subsampled_rids sub
                       WHERE  sub.rid = src.rid
                    );
                    """
                )

                logger.debug("Deleting rows from links (source)...")
                cur.execute(
                    """
                    DELETE FROM links src
                    WHERE NOT EXISTS (
                       SELECT FROM subsampled_rids sub
                       WHERE  sub.rid = src.source
                    );
                    """
                )
                logger.debug("Deleting rows from links (target)...")
                cur.execute(
                    """
                    DELETE FROM links src
                    WHERE NOT EXISTS (
                       SELECT FROM subsampled_rids sub
                       WHERE  sub.rid = src.target
                    );
                    """
                )

                logger.debug("Deleting rows from current_propsheets...")
                cur.execute(
                    """
                    DELETE FROM current_propsheets src
                    WHERE NOT EXISTS (
                       SELECT FROM subsampled_rids sub
                       WHERE  sub.rid = src.rid
                    );
                    """
                )

                logger.debug("Deleting rows from propsheets...")
                cur.execute(
                    """
                    DELETE FROM propsheets src
                    WHERE NOT EXISTS (
                       SELECT FROM subsampled_rids sub
                       WHERE  sub.rid = src.rid
                    );
                    """
                )

                logger.info("Recovering constraints of tables...")

                logger.debug("Recovering constraints of current_propsheets...")
                cur.execute(
                    """
                    ALTER TABLE current_propsheets
                      ADD CONSTRAINT "current_propsheets_rid_fkey"
                      FOREIGN KEY (rid) REFERENCES resources(rid);
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE current_propsheets
                      ADD CONSTRAINT "current_propsheets_sid_fkey"
                      FOREIGN KEY (sid) REFERENCES propsheets(sid);
                    """
                )

                logger.debug("Recovering constraints of keys...")
                cur.execute(
                    """
                    ALTER TABLE keys
                      ADD CONSTRAINT "keys_rid_fkey"
                      FOREIGN KEY (rid) REFERENCES resources(rid);
                    """
                )

                logger.debug("Recovering constraints of links...")
                cur.execute(
                    """
                    ALTER TABLE links
                      ADD CONSTRAINT "links_source_fkey"
                      FOREIGN KEY (source) REFERENCES resources(rid);
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE links
                      ADD CONSTRAINT "links_target_fkey"
                      FOREIGN KEY (target) REFERENCES resources(rid);
                    """
                )

                logger.debug("Recovering constraints of propsheets...")
                cur.execute(
                    """
                    ALTER TABLE propsheets
                      ADD CONSTRAINT "fk_property_sheets_rid_name"
                      FOREIGN KEY (rid, name) REFERENCES current_propsheets(rid, name)
                      DEFERRABLE INITIALLY DEFERRED;
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE propsheets
                      ADD CONSTRAINT "propsheets_rid_fkey"
                      FOREIGN KEY (rid) REFERENCES resources(rid)
                      DEFERRABLE INITIALLY DEFERRED;
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE propsheets
                      ADD CONSTRAINT "propsheets_tid_fkey"
                      FOREIGN KEY (tid) REFERENCES transactions(tid)
                      DEFERRABLE INITIALLY DEFERRED;
                    """
                )

        logger.info("Transaction 3: Cleaning up temp tables.")

        with self.database.conn:
            with self.database.conn.cursor() as cur:

                logger.info("Dropping a temp table...")
                cur.execute(
                    """
                    Drop TABLE subsampled_rids;
                    """
                )

        logger.info("Transaction 4: Free up deleted rows.")

        self.database.vacuum()

        logger.info("subsampling PG is all done.")
