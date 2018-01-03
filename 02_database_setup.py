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
		"block			INT			PRIMARY KEY,"
		"hash			CHAR(64)	BINARY UNIQUE,"
		"confirmations INT,"
		"merkleroot    CHAR(64)		BINARY,"
		"miner         CHAR(36)		BINARY,"
		"bits          CHAR(8),"
		"difficulty    FLOAT,"
		"transactions  INT,"
		"date          DATETIME"
	")"
));

sql.execute((
	"CREATE TABLE transactions ("
		"hash			CHAR(64)	BINARY PRIMARY KEY,"
		"block			INT," 						# parent block height
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
		"hash			CHAR(64)	BINARY,"		# parent transaction
		"prevhash		CHAR(64)	BINARY,"
		"idx			INT,"
		"type			INT," 						# type - 0 in, 1 out, 2 joinsplit
		"addr			CHAR(36)	BINARY,"
		"value			BIGINT,"
		"script			TEXT,"
		"INDEX hash_index(hash),"
		"INDEX prevhash_index(prevhash),"
		"INDEX address(addr,type)"
	")"
));
print("created tables:")
sql.execute("SHOW TABLES")
res = sql.fetchall()
print(res)
######################################
import pickle
DATA_DIR = "./data/"

c = 0
for fn in os.listdir(DATA_DIR):
	fp = DATA_DIR + fn
	if len(fn) != 64 + 8:
		continue

	c += 1
	with open(fp, "rb") as f:
		blk = pickle.load(f)

	print("[{}] processing {} ({})".format(c,blk.coinbase.inputs[0].height, blk.blockhash))

	# process coinbase transaction
	t = blk.coinbase
	sql.execute(
		"INSERT INTO transactions (hash, block, input, output, joinsplit, locktime, version, date) VALUES ('{}','{}',{},{},{},{},{},from_unixtime({}))"
		.format(
			t.txid,
			blk.coinbase.inputs[0].height,
			len(t.inputs),
			len(t.outputs),
			len(t.joinsplits),
			t.lock_time,
			t.version,
			blk.header.nTime
		)
	)

	for ti in blk.coinbase.inputs:
		sql.execute(
			"INSERT INTO transaction_inouts (hash, prevhash, idx, type, addr, value, script) VALUES ('{}', '{}', {}, {}, NULL, {}, '{}')"
			.format(
				t.txid,
				ti.prevhash,
				int(ti.index,16),
				0,
				0,
				ti.script
			)
		)

	block_miner = blk.coinbase.outputs[0].script.address
	cnt = 0
	for to in blk.coinbase.outputs:
		sql.execute(
			"INSERT INTO transaction_inouts (hash, prevhash, idx, type, addr, value, script) VALUES ('{}', NULL, {},  {}, '{}', {}, '{}')"
			.format(
				t.txid,
				cnt, # int(to.index,16),
				1,
				to.script.address,
				to.value,
				to.rawdata
			)
		)
		cnt += 1

	# process ordinary transactions
	for t in blk.transactions:
		sql.execute(
			"INSERT INTO transactions (hash, block, input, output, joinsplit, locktime, version, date) VALUES ('{}','{}',{},{},{},{},{},from_unixtime({}))"
			.format(
				t.txid,
				blk.coinbase.inputs[0].height,
				len(t.inputs),
				len(t.outputs),
				len(t.joinsplits),
				t.lock_time,
				t.version,
				blk.header.nTime
			)
		)

		for ti in t.inputs:
			sql.execute(
				"INSERT INTO transaction_inouts (hash, prevhash, idx, type, addr, value, script) VALUES ('{}', '{}', {}, {}, NULL, {}, '{}')"
				.format(
					t.txid,
					ti.prevhash,
					int(ti.index,16),
					0,
					0,
					ti.script
				)
			)

		cnt = 0
		for to in t.outputs:
			sql.execute(
				"INSERT INTO transaction_inouts (hash, prevhash, idx, type, addr, value, script) VALUES ('{}', NULL, {}, {}, '{}', {}, '{}')"
				.format(
					t.txid,
					cnt, #int(to.index,16),
					1,
					to.script.address,
					to.value,
					to.rawdata
				)
			)
			cnt += 1

	# add block information at last, to determine the miner in advance.
	sql.execute(
		"INSERT INTO blocks (hash, block, confirmations, merkleroot, miner, bits, difficulty, transactions, date) VALUES ('{}', {}, NULL, '{}', '{}', '{}', {}, {}, from_unixtime({}) )"
		.format(
			blk.blockhash,
			blk.coinbase.inputs[0].height,
			blk.header.MerkleRoot,
			block_miner,
			blk.header.nBits,
			blk.header.difficulty,
			len(blk.transactions) + 1, # coinbase + non_coinbase
			blk.header.nTime
		)
	)

	#if c == 150:
	#	break
con.commit()
