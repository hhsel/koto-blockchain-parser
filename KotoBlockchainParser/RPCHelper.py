import json
import requests

with open("config.json", "r") as f:
	o = json.load(f)
for k in o:
	globals()[k] = o[k]

COIND_URL = "{}://{}:{}".format( COIND_PROTOCOL, COIND_DOMAIN, COIND_PORT )

def get_rawblockdata(blockhash):
	params = {
		"jsonrpc": "2.0",
		"method": "getblock",
		"params": [blockhash, False],
		"id": 1
	}

	r = requests.post(COIND_URL, auth=(COIND_USER, COIND_PASS), data=json.dumps(params) )
	r.raise_for_status()
	o = r.json()
	return o["result"]
