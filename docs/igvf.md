## Running the subsampler with a RDS Database (IGVF)

1) Login on AWS Console and go to [RDS](https://us-west-2.console.aws.amazon.com/rds/home?region=us-west-2#databases:). Take a snapshot of existing DB (dev or production) and restore it on a new RDS instance.

2) Copy VPC ID of the RDS instance. Click on `Actions` and then `Set up EC2 connection`. Create a new small EC2 instance with OS `Ubuntu` and specify the same VPC ID.

3) Go back to RDS instance on AWS Console. Click on `Actions` and then `Set up EC2 connection`. Connect it to the new EC2 instance. Copy DB hostname (endpoint) and port.

4) Get DB master password from [Secrets Manager](https://us-west-2.console.aws.amazon.com/secretsmanager/listsecrets?region=us-west-2&search=all%3Digvfddev). Retrieve secret value for `password`.

4) SSH to the EC2 instance and install Postgresql and start the service. Login as `postgres`. and install this tool. You are ready to run the tool.
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
$ create_rule_template -o subsampling_rule.json -d igvfd -P PASSWORD --host RDS_INSTANCE_HOSTNAME
```

6) Create subsample UUIDs CSV file based on the rule JSON.
```bash
$ get_subsampled_uuids subsampling_rule.json -o subsampled.csv -d igvfd -P PASSWORD --host RDS_INSTANCE_HOSTNAME
```

7) Use the CSV file to subsample PG DB.
```bash
$ subsample_pg subsampled.csv -d igvfd -P PASSWORD --host RDS_INSTANCE_HOSTNAME
```

## Running the subsampler on a demo machine (ENCODE)

See [this document](/docs/installation_on_encode_demo_machine for details.md).
