## igvf-subsample-db

This tools subsamples Postgres DB of ENCODE/IGVF servers

## Installation
Edit `/etc/postgresql/11/main/pg_hba.conf` (md5 -> trust) to allow local connection.

```
# IPv4 local connections:
#host    all             all             127.0.0.1/32            md5
host    all             all             127.0.0.1/32            trust
```
