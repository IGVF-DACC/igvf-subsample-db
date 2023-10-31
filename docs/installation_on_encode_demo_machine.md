## Deploying a new ENCODE demo instance

See https://github.com/ENCODE-DCC/encoded#deploying-an-aws-demo for ENCODE and 

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

$ create_rule_template -o subsampling_rule.json -p encoded
```

Edit the template rule JSON file or use your own. Run the tool to get a CSV file with subsampled UUIDs.
```bash
$ get_subsampled_uuids subsampling_rule.json -o subsampled.csv -p encoded
```

Make a backup of the database.
```bash
$ psql
> CREATE DATABASE encoded_backup WITH TEMPLATE encoded;
```

Take the CSV file and feed it to the subsampler, this will directly modify the current PG database.
```bash
$ subsample_pg subsampled.csv -p encoded
```

Login as `encoded`. Reindex ElasticSearch.
```bash
$ sudo su encoded # or igvfd

# check indices first
$ curl -X GET 'localhost:9201/_cat/indices'

# delete indices
$ curl -X DELETE 'http://localhost:9201/_all'

# check if all indices are deleted
$ curl -X GET 'localhost:9201/_cat/indices'

# reindex ES
$ create-mapping production.ini --app-name app

# check if all indices are back
$ curl -X GET localhost:9201/_cat/indices
```

Wait for 30m and login as `root` and then start the web server.
```bash
$ service apache2 start
```

Visit the demo site and login as an admin account. Run the reindexer via URL. Open URL `YOUR_DEMO_ENDPOINT/_indexer_state?reindex=all`.
