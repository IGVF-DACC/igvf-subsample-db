## Creating a new demo machine testing

See [this document](https://github.com/ENCODE-DCC/encoded#deploying-an-aws-demo) for details.


## Running the subsampler on a demo machine (ENCODE)

SSH to a demo instance, login as `root` and stop web server and ES.
```bash
$ service apache2 stop
$ service elasticsearch stop
```

Login as `postgres` and install the tool.
```bash
$ sudo su postgres
$ cd

# install the tool from pip
$ pip3 install igvf-subsample-db

# install the tool from setup.py
$ git clone https://github.com/igvf-dacc/igvf-subsample-db
$ cd igvf-subsample-db
$ python3 setup.py install --user
```

Edit `/etc/postgresql/11/main/pg_hba.conf` (md5 -> trust) to allow local connection from the tool.
```
# IPv4 local connections:
#host    all             all             127.0.0.1/32            md5
host    all             all             127.0.0.1/32            trust
```

(Optional) Create a template rule JSON. You can find more [examples](/examples) on this repo.
```bash
$ create_rule_template -o subsampling_rule.json -d encoded
```

Edit the template rule JSON file or use your own. Run the tool to get a CSV file with subsampled UUIDs.
```bash
$ get_subsampled_uuids subsampling_rule.json -o subsampled.csv -d encoded
```

Make a backup of the database.
```bash
$ psql
> CREATE DATABASE encoded_backup WITH TEMPLATE encoded;
```

Take the CSV file and feed it to the subsampler, this will directly modify the current PG database.
```bash
$ subsample_pg subsampled.csv -d encoded
```

If you see the following deadlock errors. Stop any process trying to connect to the DB (e.g. apache2, ES). Stop those services and try again.
```bash
Traceback (most recent call last):
  File "bin/subsample_pg", line 13, in <module>
    main()
  File "/var/lib/postgresql/igvf-subsample-db/bin/../igvf_subsample_db/subsample_pg.py", line 65, in main
    profiles.subsample_pg(args.uuids_csv)
  File "/var/lib/postgresql/igvf-subsample-db/bin/../igvf_subsample_db/profiles.py", line 279, in subsample_pg
    cur.execute(
psycopg2.errors.DeadlockDetected: deadlock detected
DETAIL:  Process 18405 waits for AccessExclusiveLock on relation 16418 of database 16401; blocked by process 20451.
Process 20451 waits for AccessShareLock on relation 16392 of database 16401; blocked by process 18405.
HINT:  See server log for query details.
```

Login as `root` and Start ES.
```bash
$ service elasticsearch start
```

Login as `encoded`. Reindex ElasticSearch.
```bash
$ sudo su encoded

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

Wait for 30m and login as `root` and then start web server.
```bash
$ service apache2 start
```

Visit the demo site and login as an admin account. Run the reindexer via URL. Open URL `YOUR_DEMO_ENDPOINT/_indexer_state?reindex=all`.
