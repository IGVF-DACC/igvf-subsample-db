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
        """Wrapper for SELECT.
        """
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
