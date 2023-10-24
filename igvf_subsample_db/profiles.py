import logging
import math
import random
from collections import defaultdict


logger = logging.getLogger(__name__)


SUBSAMPLING_RANDOM_SEED = 17
UUIDS_PER_LOG = 500


class Profiles:
    def __init__(self, database):
        """
        Member vars:
            self.links:
                A dict of {source_uuid: [target_uuids...]}
            self.resources:
                A dict of {profile_name: [uuids...]}
            self.uuid_to_profile:
                A dict of {uuid: profile_name}
        """
        self.database = database

        logger.info("Loading links from DB...")
        self.links = defaultdict(set)
        for source_uuid, rel, target_uuid in self.database.send_query(
            "SELECT * FROM links"
        ):
            self.links[source_uuid].add(target_uuid)

        logger.info("Loading resources from DB...")
        # self.resources = defaultdict(set)
        self.uuid_to_profile = {}
        for uuid, profile_name in self.database.send_query(
            "SELECT * FROM resources"
        ):
            # self.resources[profile_name].add(uuid)
            self.uuid_to_profile[uuid] = profile_name

        logger.info("Loading distinct profiles from DB...")
        self.profile_names = set()

        for profile_name, in self.database.send_query(
            "SELECT DISTINCT(item_type) FROM resources"
        ):
            self.profile_names.add(profile_name)

        self._uuids = set()

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

                query = f"SELECT rid FROM object WHERE item_type='{profile_name}' {cond_sql}"

                logger.info(
                    f"Subsampling for profile {profile_name} with "
                    f"cond {subsampling_cond}, Query: {query}"
                )

                uuids = []
                for uuid, in self.database.send_query(query):
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
        if uuid in self._uuids:
            return

        if uuid in parent_uuids:
            logger.debug(f"Cyclic ref found. {depth}: {uuid}, {self.uuid_to_profile[uuid]}")
            return

        if depth > 300:
            logger.debug(f"Search tree is too deep. {depth}: {uuid}, {self.uuid_to_profile[uuid]}")

        self._uuids.add(uuid)

        parent_uuids += (uuid,)
        depth += 1

        if len(self._uuids) % UUIDS_PER_LOG == 0:
            logger.info(f"Number of UUIDs = {len(self._uuids)} so far.")

        for linked_uuid in self.links(uuid):
            self.add_uuid(linked_uuid, depth=depth, parent_uuids=parent_uuids)
