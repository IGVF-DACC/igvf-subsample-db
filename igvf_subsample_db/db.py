import psycopg2


class Database:
    def __init__(self, database, user="postgres", password="postgres", host="127.0.0.1", port=5432):
        self.conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
        )

    def __del__(self):
        self.conn.close()

    def fetchall(self, query):
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def commit(self, query):
        self.conn.cursor().execute(query)
        self.conn.commit()

class SubsampleDatabase:
    def __init__(self, database):
        """
        Args:
            database: Database object
        """
        self.database = database

    def subsampleDatabase(self, uuids):
        pass

    def _drop_constraints(self):
        pass

    def _rebuild_constraints(self):
        pass
