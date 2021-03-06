from KotoBlockchainParser import Block
import mysql.connector
import json
import os

TRANSACTION_INDEX_NULL = 2147483647 # 0xFFFFFFFF

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
sql = con.cursor()

print("re-creating addresses table..")
sql.execute("DROP TABLE IF EXISTS addresses")
sql.execute((
	"CREATE TABLE addresses ("
		"address		CHAR(36)	BINARY PRIMARY KEY,"
		"balance		BIGINT,"
		"sent			BIGINT,"
		"received  		BIGINT,"
		"minedblocks	INT,"
		"create_date	DATETIME,"
		"update_date	DATETIME"
	")"
));
print("filling basic information")
sql.execute((
	"INSERT INTO addresses (address, balance, update_date, create_date, minedblocks)"
	"(SELECT addr, SUM(value), MAX(date), MIN(date), 0 FROM transaction_inouts "
	"INNER JOIN transactions USING(hash) WHERE addr IS NOT NULL AND addr!='None' GROUP BY addr)"
))

print("calculating mined blocks")
sql.execute((
	"UPDATE addresses "
	"INNER JOIN (SELECT miner, COUNT(miner) AS cnt FROM blocks WHERE miner IS NOT NULL AND miner != 'None' GROUP BY miner)"
	"	AS tmp ON tmp.miner=addresses.address "
	"SET addresses.minedblocks = tmp.cnt"
))

print("calculating total sent")
sql.execute((
	"UPDATE addresses "
	"INNER JOIN (SELECT addr, SUM(value) AS value FROM transaction_inouts "
	"	WHERE type=0 GROUP BY addr)"
	"AS tmp ON tmp.addr=addresses.address "
	"SET addresses.sent = tmp.value"
))

print("calculating total received")
sql.execute((
	"UPDATE addresses "
	"INNER JOIN (SELECT addr, SUM(value) AS value FROM transaction_inouts "
	"	WHERE type=1 GROUP BY addr)"
	"AS tmp ON tmp.addr=addresses.address "
	"SET addresses.received = tmp.value"
))

con.commit()
print("done")
