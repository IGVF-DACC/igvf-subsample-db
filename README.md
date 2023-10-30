# IGVF Subsample DB

This tool subsamples Postgres database of ENCODE/IGVF servers based on a subsampling rule JSON file. It will generate a list subsampled UUIDs and find all linked UUIDs recursively. And then it will remove all other UUIDs from the database.


## Subsampling rule JSON

This file defines subsampling rule(s) for each profile (e.g. `experiment` for ENCODE, `measurement_set` for IGVF). Multiple rules are allowed for each profile. Here is an example for ENCODE:
```json
{
    "file": [
        {
            "subsampling_min": 100,
            "subsampling_rate": 1e-03
        }
    ],
    "experiment": [
        {
            "subsampling_min": 3,
            "subsampling_rate": 1e-05,
            "subsampling_cond": {
                "assay_term_name": "ATAC-seq"
            }
        },
        {
            "subsampling_min": 5,
            "subsampling_rate": 1e-05,
            "subsampling_cond": {
                "assay_term_name": "ChIP-seq"
            }
        }
	]
}
```

A rule is consist of `subsampling_min`, `subsampling_rate` and `subsampling_cond` (optional). See the following example of `experiment` profile of ENCODE.
```json
{
    "subsampling_min": 5,
    "subsampling_rate": 1e-05,
    "subsampling_cond": {
        "assay_term_name": "ChIP-seq"
    }
}
```

* `subsampling_min` defines the minimum number of objects in the profile after subsampling.
* `subsampling_rate` defines the minimum number of objects as total number of objects in the profile multiplied by the rate. MAX of these two values will be taken as the final number of subsampled objects in the profile.
* `subsampling_cond` is a JSON object that defines conditions for the rule. For the above example, this will only subsample objects with a property `assay_term_name` defined as `ChIP-seq`. You can use any valid property in a profile. See profile's schema JSON to find such property.

There are currently `12548` `ChIP-seq` experiments and it will subsample `12548` objects down to `MAX(5, 1e-05*12548)=5`.

For the case of `file` profile in the above example, there are currently `1458539` `file` objects on ENCODE. So it will subsample `1458539` objects down to `MAX(100, 1e-03 * 1458539) = 1458`.

You can have multiple rules under a single profile. See the case of `experiment` profile in the above example. It will include at least 3 `ATAC-Seq` experiments and 5 `ChIP-seq` experiments.


## Deploying a new demo instance

Since the tool directly modifies the PG database on a demo instance, you need to spin up a new demo instance first.

See https://github.com/ENCODE-DCC/encoded#deploying-an-aws-demo for ENCODE and https://github.com/IGVF-DACC/igvfd/blob/dev/cdk/README.md for IGVF.


## Running the subsampler

SSH to a demo instance, login as `root` and stop a web server.
```bash
$ service apache2 stop
```

Login as `postgres` and install the tool.
```bash
$ sudo su postgres
$ pip install igvf_subsample_db
```

Edit `/etc/postgresql/11/main/pg_hba.conf` (md5 -> trust) to allow local connection from the tool.
```
# IPv4 local connections:
#host    all             all             127.0.0.1/32            md5
host    all             all             127.0.0.1/32            trust
```

(Optional) Create a template rule JSON. You can find more [examples](/examples) on this repo.
```bash
$ PLATFORM=encode # or igvf

$ create_rule_template -o example_subsampling_rule.json -p $PLATFORM
```

Edit the template rule JSON file or use your own. Run the tool to get a CSV file with subsampled UUIDs.
```bash
$ get_subsampled_uuids [RULE_JSON_FILE] -o subsampled.csv -p $PLATFORM --debug
```

Make a backup of the database.
```bash
$ psql

# for ENCODE
> CREATE DATABASE encoded_backup WITH TEMPLATE encoded;

# for IGVF
> CREATE DATABASE igvfd_backup WITH TEMPLATE igvfd;
```

Take the CSV file and feed it to the subsampler, this will directly modify the current PG database.
```bash
$ subsample_pg [SUBSAMPLED_CSV_FILE] -p $PLATFORM --debug
```

Login as `encoded` (ENCODE) or `igvfd` (IGVF). Reindex ElasticSearch.
```bash
$ sudo su encoded # or igvfd

# check indices first
$ curl -X GET 'localhost:9201/_cat/indices'

# delete indices
$ curl -X DELETE 'http://localhost:9201/_all'

# check if all indices are deleted
$ curl -X GET 'localhost:9201/_cat/indices'

# reindex ES (ENCODE)
$ create-mapping production.ini --app-name app

# reindedx ES (IGVF)
$ ...

# check if all indices are back
$ curl -X GET localhost:9201/_cat/indices
```

Wait for 30m and login as `root` and then start the web server.
```bash
$ service apache2 start
```

Visit the demo site and login as an admin account. Run the reindexer via URL. Open URL `YOUR_DEMO_ENDPOINT/_indexer_state?reindex=all`.
