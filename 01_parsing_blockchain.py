from KotoBlockchainParser import Block
import os
import time

OUTPUT_DIR = "./data/"

blockhash = "c95868b588d28bd6d15d13274d9353c8ac22aadecf7f0fc3cc3299c30ce67e71"
# remarkable blocks
#blockhash = "e574d8fc0a69205757759ae67d2ccbfb015b3776629b6ce2638fb27aef193129"
#blockhash = "793e15fd4f18099efb86ccf350851e1a3f88fa25fd865f830c61e958128bafce"
#blockhash = "676e8985cb56c2b5f7eb01c836619954585df13d375022c23939643b77303140" # ???
#blockhash = "3e38441a1b9503e4d9fe2d685edba14c7ec7fdd8bdc2aa77378b358dfb629337"
#blockhash = "c82be49015407233dbe0444d24686580a383601d5d25140de6ccd1ebf2fc51c7" ripemd160 is in script
#blockhash = "6d424c350729ae633275d51dc3496e16cd1b1d195c164da00f39c499a2e9959e" # genesis block

tolerance = 10
tc = 0
while True:
	print("* processing: {}".format(blockhash))
	try:
		blk = Block.fromBlockHash(blockhash)
		height = blk.coinbase.inputs[0].height
		print("done, (block height {}, {} transactions found)".format(
					height,
					len(blk.transactions)+1
		))
		tc = 0
	except Exception:
		tc += 1
		print("connection failed {}".format(tc))
		import traceback
		traceback.print_exc()
		time.sleep(5)
		if tc > 10:
			print("ERROR!")
			exit()
		continue

	fp = OUTPUT_DIR + "{}_{}".format( str(height).zfill(7), blockhash)
	blk.serialize(fp)
	print("output to {}".format(fp))
	if blk.coinbase.inputs[0].height == 0:
		break

	blockhash = blk.header.prevBlockHash

print("PASSED ALL TEST CASES")
