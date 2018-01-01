from KotoBlockchainParser import Block
import mysql.connector
import json
import os

import pickle
DATA_DIR = "./data/"

c = 0
for fn in os.listdir(DATA_DIR):
	fp = DATA_DIR + fn
	if len(fn) != 64:
		continue

	c += 1
	with open(fp, "rb") as f:
		blk = pickle.load(f)

	print("[{}] processing {} ({})".format(c,blk.coinbase.inputs[0].height, blk.blockhash))
	print(blk)
	if c == 6: break
