import psycopg2


class Database:
    def __init__(self, database, user="postgres", password="postgres", host="127.0.0.1", port=5432):
        self.connection = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
        )
        self.cursor = self.connection.cursor()

    def send_query(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()


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
