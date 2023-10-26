# IGVF Subsample DB

This tool subsamples Postgres database of ENCODE/IGVF servers based on a subsampling rule JSON file. 
It directly modifies the Postgres database of a demo instance. So you need to spin up a new demo instance and stop the web server first.


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

* `subsampling_min` defines the minimum number of objects in the profile.
* `subsampling_rate` defines the minimum number of objects as total number of objects in the profile multiplied by the rate. MAX of these two values will be taken as the final number of subsampled objects in the profile.
* `subsampling_cond` is a JSON object that defines conditions for the rule. For the above example, this will only subsample objects with a property `assay_term_name` defined as `ChIP-seq`. You can use any valid property in a profile. See profile's schema JSON to find such property.

There are currently `12548` `ChIP-seq` experiments and it subsample `12548` objects down to `MAX(5, 1e-05*12548)=5`.

For the case of `file` profile in the above example, there are currently `1458539` `file` objects on ENCODE. So it will subsample `1458539` objects down to `MAX(100, 1e-03 * 1458539) = 1458`.

You can have multiple rules under a single profile. See the case of `experiment` profile in the above example. It will include at least 3 `ATAC-Seq` experiments and 5 `ChIP-seq` experiments.


## Deploying a new demo instance (ENCODE)

See https://github.com/ENCODE-DCC/encoded#deploying-an-aws-demo to deploy a new demo instance for ENCODE.


## Deploying a new demo instance (IGVF)

See https://github.com/IGVF-DACC/igvfd/blob/dev/cdk/README.md to deploy a new demo instance for IGVF.


## Running the subsampler

SSH to the instance and stop the web server.
```bash
# login as root
$ service apache2 stop
```

Edit `/etc/postgresql/11/main/pg_hba.conf` (md5 -> trust) to allow local connection from the tool.
```
# IPv4 local connections:
#host    all             all             127.0.0.1/32            md5
host    all             all             127.0.0.1/32            trust
```

Login as `postgres` user and install the tool.
```bash
$ sudo su postgres
$ pip install igvf_subsample_db
```

Define your platform (ENCODE or IGVF). Run the UUID subsampler or get the template rule JSON first.
```bash
$ PLATFORM=ENCODE # or IGVF

# login as postgres
$ sudo su postgres

# get a template rule JSON first
# this teamplate will include all profiles defined in the database
$ igvf_subsample_db -p $PLATFORM create_rule_template example_subsampling_rule.json
```

Edit the template rule JSON file or use your own. Run the tool to get a CSV (with header `rid`) file with subsampled UUIDs.
```bash
$ igvf_subsample_db -p $PLATFORM get_subsampled_uuids [RULE_JSON_FILE] -o subsampled.csv --debug
```

Make a backup of the database.
```bash
$ psql

# for ENCODE
> CREATE DATABASE encoded_backup WITH TEMPLATE encoded;

# for IGVF
> CREATE DATABASE igvfd_backup WITH TEMPLATE igvfd;
```

Take the CSV file and feed it to the subsampler, this will directly modify the current pg database.
```bash
$ igvf_subsample_db -p $PLATFORM subsample_pg [SUBSAMPLED_CSV_FILE] --debug
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
$ create-mapping production.ini --app-name app

# check if all indices are back
$ curl -X GET localhost:9201/_cat/indices
```

Wait for 30m and login as `root` and then start the web server back on.
```bash
$ service apache2 start
```

Visit the demo site and login as an admin. Run reindexer via URL. Open URL `YOUR_DEMO_ENDPOINT/_indexer_state?reindex=all`.
