from KotoBlockchainParser import Block
import mysql.connector
import json
import os

with open("config.json", "r") as f:
	o = json.load(f)
for k in o:
	globals()[k] = o[k]

con = mysql.connector.connect(
    host = DB_HOST,
    port = DB_PORT,
    user = DB_USER,
    password = DB_PASSWORD,
    database = DB_NAME
)
sql = con.cursor(buffered=True)

########################################### DERIVED INFORMATION
		# "address		CHAR(36)	PRIMARY KEY,"
		# "balance		INT,"
		# "minedblocks	INT,"
		# "create_date	DATETIME,"
		# "update_date	DATETIME"
		# transaction_inouts (hash, prevhash, type, addr, value, script

# sql.execute(
#  	"INSERT INTO addresses (address, balance) (SELECT addr, SUM(value) FROM transaction_inouts GROUP BY addr)"
# )
sql.execute((
 	"SELECT hash,prevhash FROM transaction_inouts "
	"WHERE type=0 AND prevhash != '0000000000000000000000000000000000000000000000000000000000000000' AND prevhash IS NOT NULL AND prevhash != ''"
	"LIMIT 1"
))
#res = sql.fetchall()
print("fetched previous hash transactions")
res = sql.fetchall()
for e in res:
	print("txid: ", e[0])
	print("prev: ", e[1])

	sql.execute((
	 	"SELECT hash, prevhash FROM transaction_inouts "
		"WHERE type=1 AND hash='{}'"
		.format(
			e[1]
		)
	))
	ins = sql.fetchall()
	print(ins)

con.commit()
