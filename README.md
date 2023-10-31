# IGVF Subsample DB

This tool subsamples Postgres database of ENCODE/IGVF servers based on a subsampling rule JSON file.

## Subsampling rule JSON

This file defines subsampling rule(s) for each profile (e.g. `experiment` for ENCODE, `measurement_set` for IGVF). Multiple rules are allowed for each profile. Here is an example for ENCODE.
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
* `subsampling_rate` defines the minimum number of objects as total (respecting `subsampling_cond` if defined) number of objects in the profile multiplied by the rate. MAX of these two values will be taken as the final number of subsampled objects in the profile.
* `subsampling_cond` is a JSON object that defines conditions for the rule. For the above example, this will only subsample objects with a property `assay_term_name` defined as `ChIP-seq`. You can use any valid property in a profile. See profile's schema JSON to find such property.

There are currently `12548` `ChIP-seq` experiments and it will subsample `12548` objects down to `MAX(5, 1e-05*12548) = 5`.

For the case of `file` profile in the above example, there are currently `1458539` `file` objects on ENCODE. So it will subsample `1458539` objects down to `MAX(100, 1e-03 * 1458539) = 1458`.

You can have multiple rules under a single profile. See the case of `experiment` profile in the above example. It will include at least 3 `ATAC-Seq` experiments and 5 `ChIP-seq` experiments.


## Running the subsampler with a RDS Database (IGVF)

1) Login on AWS Console and go to [RDS](https://us-west-2.console.aws.amazon.com/rds/home?region=us-west-2#databases:). Take a snapshot of existing DB (dev or production) and restore it on a new RDS instance. `Modify` the new instance and give it a new master password.

2) Copy VPC ID of the RDS instance. Click on `Actions` and then `Set up EC2 connection`. Create a new small EC2 instance with OS `Ubuntu` and specify the same VPC ID.

3) Go back to RDS instance on AWS Console. Click on `Actions` and then `Set up EC2 connection`. Connect it to the new EC2 instance. Copy DB hostname (endpoint) and port.

4) SSH to the EC2 instance and install Postgresql and start the service. Login as `postgres` with the master password. and install this tool. You are ready to run the tool. `DATABASE_NAME` is `encoded` for ENCODE and `igvfd` for IGVF.
```bash
$ sudo apt-get update -y
$ sudo apt-get install postgresql python3-pip libpq-dev -y
$ sudo service postgresql start

# Login as postgres
$ sudo su postgres
$ cd
$ pip3 install igvf-subsample-db # or python3 setup.py install
```

5) (Optional) Create a template rule JSON and edit it. You can also use example rules on `examples/` folder.
```bash
$ create_rule_template -o subsampling_rule.json -d DATABASE_NAME -P PASSWORD --host RDS_INSTANCE_HOSTNAME
```

6) Create subsample UUIDs CSV file based on the rule JSON.
```bash
$ get_subsampled_uuids subsampling_rule.json -o subsampled.csv -P PASSWORD --host RDS_INSTANCE_HOSTNAME
```

7) Use the CSV file to actually subsample PG DB.
```bash
$ subsample_pg subsampled.csv -d DATABASE_NAME -P PASSWORD --host RDS_INSTANCE_HOSTNAME
```

## Running the subsampler on a demo machine

See [this document](/docs/installation_on_encode_demo_machine for details.md).
