import sys
import requests
import json
from KotoBlockchainParser import KotoBlock

# args = sys.argv
# if len(args) != 2:
# 	print("invalid argument")
# 	exit()

# BLOCKHASH = args[1]

with open("testcase.txt","r") as f:
	ls = f.read().split("\n")[:-1]
	ls = [s[29:] for s in ls]

from config import  url, COIND_USER, COIND_PASS
for BLOCKHASH in ls:
	print("processing {}".format(BLOCKHASH))

	params = {
		"jsonrpc": "2.0",
		"method": "getblock",
		"params": [BLOCKHASH, False],
		"id": 1
	}

	r = requests.post(url, auth=(COIND_USER, COIND_PASS), data=json.dumps(params) )
	o = r.json()
	b = o["result"]

	blk = KotoBlock(b)
	#print(blk)

print("PASSED ALL TEST CASES")
