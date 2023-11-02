import psycopg2


class Database:
    def __init__(
        self,
        database,
        user="postgres",
        password="postgres",
        host="127.0.0.1",
        port=5432,
    ):
        self.conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
        )

    def __del__(self):
        self.conn.close()

    def conn(self):
        return self.conn

    def fetchall(self, query):
        """
        Wrapper for SELECT.
        """
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()

    def vacuum(self):
        """
        Workaround to run VACCUM FULL outside of a transaction
        https://stackoverflow.com/a/1017655
        """
        old_isolation_level = self.conn.isolation_level
        self.conn.set_isolation_level(0)
        self.conn.cursor().execute("VACUUM FULL")
        self.conn.commit()
        self.conn.set_isolation_level(old_isolation_level)
