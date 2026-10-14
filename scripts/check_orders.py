"""Show the table exists, count rows twice (it should grow), and print a few rows."""
import time
import snowflake.connector
from _common import ACCOUNT, ROLE, USER, der_private_key

cur = snowflake.connector.connect(account=ACCOUNT, user=USER, private_key=der_private_key(),
                                  role=ROLE, warehouse="COMPUTE_WH").cursor()
cur.execute("SHOW TABLES IN SCHEMA KAFKA_DEMO.STREAMING"); print("tables:", [r[1] for r in cur.fetchall()])
for _ in range(2):
    cur.execute("SELECT COUNT(*) FROM KAFKA_DEMO.STREAMING.ORDERS"); print("rows:", cur.fetchone()[0]); time.sleep(10)
cur.execute("SELECT ORDERID, ITEMID, ADDRESS:city::string FROM KAFKA_DEMO.STREAMING.ORDERS LIMIT 5")
for r in cur.fetchall(): print(r)
