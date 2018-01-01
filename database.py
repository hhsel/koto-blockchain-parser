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
sql = con.cursor()

print("removing all tables...")
sql.execute("SHOW TABLES")
res = sql.fetchall()
for r in res:
	r = r[0]
	print("dropping table {}".format(r))
	sql.execute("DROP TABLE {}".format(r))

print("setting up tables...")
sql.execute((
	"CREATE TABLE blocks ("
		"hash          CHAR(32)    PRIMARY KEY,"
		"height        INT,"
		"prevhash      CHAR(32),"
		"nexthash      CHAR(32),"
		"confirmations INT,"
		"merkleroot    CHAR(32),"
		"miner         CHAR(36),"
		"bits          CHAR(8),"
		"difficulty    FLOAT,"
		"transactions  INT,"
		"date          DATETIME"
	")"
));

sql.execute((
	"CREATE TABLE addresses ("
		"address		CHAR(36)	PRIMARY KEY,"
		"balance		INT,"
		"blocks			INT," # mined blocks
		"create_date	DATETIME,"
		"update_date	DATETIME"
	")"
));

sql.execute((
	"CREATE TABLE transactions ("
		"hash			CHAR(32)	PRIMARY KEY,"
		"prevhash		CHAR(32),"
		"block			CHAR(32),"
		"input			INT,"
		"output			INT,"
		"joinsplit		INT,"
		"locktime		INT,"
		"version		INT,"
		"date			DATETIME"
	")"
));

sql.execute((
	"CREATE TABLE transaction_inouts ("
		"hash			CHAR(32)," # parent transaction
		"type			INT," # type - 0 in, 1 out, 2 joinsplit
		"addr			CHAR(36),"
		"value			INT,"
		"script			TEXT"
	")"
));
print("created tables:")
sql.execute("SHOW TABLES")
res = sql.fetchall()
print(res)
######################################
import pickle
DATA_DIR = "./data/"
for fn in os.listdir(DATA_DIR):
	fp = DATA_DIR + fn
	with open(fp, "rb") as f:
		blk = pickle.load(f)

	print("processing {} ({})".format(blk.coinbase.inputs[0].height, blk.blockhash))
	exit()
