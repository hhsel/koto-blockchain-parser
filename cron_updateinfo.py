## script 00-04 is initial scripts.
# this program is executed by cron regularly, after initialization.
from KotoBlockchainParser import Block
import mysql.connector
import json
import os
print("start")
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

# if cron_logs does not exist, create the table.
def ensure_table_existence():
	sql.execute((
		"CREATE TABLE IF NOT EXISTS cron_logs ("
			"lid			INT			AUTO_INCREMENT NOT NULL PRIMARY KEY,"
			"code			INT,"
			"hash			CHAR(64)	BINARY,"
			"memo			TEXT,"
			"date         	DATETIME"
		")"
	));

try:
	ensure_table_existence()
	with open("/root/logs/latestblock.dat") as f:
		blockhash = f.read()
		blockhash = blockhash[0:-1]
		if len(blockhash) != 64:
			exit()
		# determine if update is needed
		sql.execute("SELECT block FROM blocks WHERE hash='{}'".format(blockhash))
		res = sql.fetchall()
		if res is not None and len(res) > 0:
			# if block exists, do nothing and exit
			sql.execute("INSERT INTO cron_logs (code,hash,memo,date) VALUES (0, '{}', 'The block exists and did nothing.', CURRENT_TIMESTAMP)".format(blockhash))
			con.commit()
			exit()
except Exception:
	# if block exists, do nothing and exit
	sql.execute("INSERT INTO cron_logs (code,hash,memo,date) VALUES (-2, '{}', 'init error.', CURRENT_TIMESTAMP)".format(blockhash))
	con.commit()
	exit()

# to-be-update files are now in ./data.
# here it is ensured that the block does not exist in the database, meaning need to update.
import os
DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + "/data/"

for fn in os.listdir(DATA_DIR)
	try:
		os.remove(DATA_DIR+fn)
	except Exception:
		pass

################################ STEP 1
while True:
	try:
		blk = Block.fromBlockHash(blockhash)
	except Exception:
		sql.execute("INSERT INTO cron_logs (code,hash,memo,date) VALUES (-1, '{}', 'Getting block information failed for some reason.', CURRENT_TIMESTAMP)".format(blockhash))
		con.commit()
		exit()

	height = blk.coinbase.inputs[0].height
	fp = DATA_DIR + "{}_{}".format( str(height).zfill(7), blockhash)
	blk.serialize(fp)

	blockhash = blk.header.prevBlockHash

	sql.execute("SELECT block FROM blocks WHERE hash='{}'".format(blockhash))
	res = sql.fetchall()
	if res is not None and len(res) > 0:
		break
################################ STEP 2
import pickle
c = 0
for fn in os.listdir(DATA_DIR):
	fp = DATA_DIR + fn
	if len(fn) != 64 + 8:
		continue

	c += 1
	with open(fp, "rb") as f:
		blk = pickle.load(f)

	height = blk.coinbase.inputs[0].height
	sql.execute("SELECT block FROM blocks WHERE block={}".format(height))
	res = sql.fetchall()
	if res is not None and len(res) > 0:
		# should the block exist, remove all.
		sql.execute("SELECT hash FROM transactions WHERE block={}".format(height))
		res = sql.fetchall()
		if res is None or len(res) == 0:
			raise Exception("why transaction is zero?")

		for txid in res:
			txid = txid.decode()
			sql.execute("DELETE FROM transaction_inouts WHERE hash='{}'".format(txid))

		sql.execute("DELETE FROM transactions WHERE block={}".format(height))
		sql.execute("DELETE FROM blocks WHERE block={}".format(height))

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

############################### STEP 3

for fn in os.listdir(DATA_DIR):
	fp = DATA_DIR + fn
	if len(fn) != 64 + 8:
		continue
	with open(fp, "rb") as f:
		blk = pickle.load(f)

	cur_height = blk.coinbase.inputs[0].height
	# get tranactions in current block height.
	sql.execute("SELECT hash FROM transactions WHERE block={}".format(cur_height))
	tx_hashes = sql.fetchall()
	print("{} transaction(s) found to look at:".format(len(tx_hashes)))
	for (txid,) in tx_hashes:
		txid = txid.decode() # hash values are binary data (case-sensitive). need to decode
		# get transaction inputs
		sql.execute("SELECT prevhash, idx FROM transaction_inouts WHERE hash='{}' AND type=0 AND prevhash!='0000000000000000000000000000000000000000000000000000000000000000'".format(txid))
		txins = sql.fetchall()
		print(txins)

		# search for corresponding (hash, index) combination
		for (prevhash, prevhashindex,) in txins:
			prevhash = prevhash.decode()
			sql.execute("SELECT addr, value FROM transaction_inouts WHERE hash='{}' AND idx={} AND type=1"
			.format(prevhash, prevhashindex))
			rdms = sql.fetchall()
			if rdms is None or len(rdms) == 0:
				raise Exception("hash-index not found")
			if len(rdms) > 1:
				raise Exception("unexpected row count > 1")
			(addr, value) = rdms[0]
			addr = addr.decode()
			print(prevhash, prevhashindex, addr, value)
			sql.execute("UPDATE transaction_inouts SET addr='{}', value={} WHERE prevhash='{}' AND idx={} AND type=0"
			.format(addr, value * (-1), prevhash, prevhashindex))

################################ STEP 4
sql.execute((
	"INSERT INTO addresses (address, balance, update_date, create_date, minedblocks)"
	"SELECT tmp.addr, tmp.total, tmp.ndate, tmp.odate, 0 FROM "
	"(SELECT addr, SUM(value) AS total, MAX(date) AS ndate, MIN(date) AS odate FROM transaction_inouts "
	"INNER JOIN transactions USING(hash) WHERE addr IS NOT NULL AND addr!='None' GROUP BY addr) AS tmp "
	"ON DUPLICATE KEY UPDATE "
	"balance = tmp.total, update_date = tmp.ndate, create_date = tmp.odate"
))

sql.execute((
	"UPDATE addresses "
	"INNER JOIN (SELECT miner, COUNT(miner) AS cnt FROM blocks WHERE miner IS NOT NULL AND miner != 'None' GROUP BY miner)"
	"	AS tmp ON tmp.miner=addresses.address "
	"SET addresses.minedblocks = tmp.cnt"
))

sql.execute((
	"UPDATE addresses "
	"INNER JOIN (SELECT addr, SUM(value) AS value FROM transaction_inouts "
	"	WHERE type=0 GROUP BY addr)"
	"AS tmp ON tmp.addr=addresses.address "
	"SET addresses.sent = tmp.value"
))

sql.execute((
	"UPDATE addresses "
	"INNER JOIN (SELECT addr, SUM(value) AS value FROM transaction_inouts "
	"	WHERE type=1 GROUP BY addr)"
	"AS tmp ON tmp.addr=addresses.address "
	"SET addresses.received = tmp.value"
))

sql.execute("INSERT INTO cron_logs (code,hash,memo,date) VALUES (100, NULL, 'Update successully done.', CURRENT_TIMESTAMP)")

con.commit()
exit()
