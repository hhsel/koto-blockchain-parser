##### SENDER ADDRSS FILLER SCRIPT
# just inserting parsed data into a database is not enough for balance calculation
# since tranasction data does not include the sender address, but the pointer of that instead.
# we need to look up each input (previous hash, previous index) and copy address, value into that input row as sender,
# which is what this script does.

from KotoBlockchainParser import Block
import mysql.connector
import json
import binascii
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

########################################### A. filling empty columns in the transaction_inouts
cur_height = 0
while True:
	# block existence check
	print("current height: {}".format(cur_height))
	sql.execute("SELECT block FROM blocks WHERE block={}".format(cur_height))
	res = sql.fetchall()
	if res is None or len(res) == 0:
		print("block number {} not found, exit.".format(cur_height))
		break

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
				print("hash {} with index {} not found".format(prevhash, prevhashindex))
				break
			if len(rdms) > 1:
				raise Exception("unexpected row count > 1")
			(addr, value) = rdms[0]
			addr = addr.decode()
			print(prevhash, prevhashindex, addr, value)
			sql.execute("UPDATE transaction_inouts SET addr='{}', value={} WHERE prevhash='{}' AND idx={} AND type=0"
			.format(addr, value * (-1), prevhash, prevhashindex))

		con.commit()
	cur_height += 1
print("done")
exit()
