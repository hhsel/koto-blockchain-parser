# first run this script to know whether successing programs will work.
from KotoBlockchainParser import Block
import mysql.connector

print("fetching a block data")
blockhash = "e574d8fc0a69205757759ae67d2ccbfb015b3776629b6ce2638fb27aef193129"
blk = Block.fromBlockHash(blockhash)
print("...OK")

print("database access")
con = mysql.connector.connect(
    host = DB_HOST,
    port = DB_PORT,
    user = DB_USER,
    password = DB_PASSWORD,
    database = DB_NAME
)
sql = con.cursor()

sql.execute("SHOW TABLES")
res = sql.fetchall()
for r in res:
	r = r[0]
	print("table {}".format(r))
print("...OK")
print("TEST PASSED)
