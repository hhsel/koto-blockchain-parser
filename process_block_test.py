from KotoBlockchainParser import Block
import os
import time

OUTPUT_DIR = "./data/"

blockhash = "e2c9c63a545e02898e35d1cf8d01b24e6a82da83f6c9a08cdb4c85d07fad69d0"

# remarkable blocks
#blockhash = "e574d8fc0a69205757759ae67d2ccbfb015b3776629b6ce2638fb27aef193129"
#blockhash = "793e15fd4f18099efb86ccf350851e1a3f88fa25fd865f830c61e958128bafce"
#blockhash = "676e8985cb56c2b5f7eb01c836619954585df13d375022c23939643b77303140" # ???
#blockhash = "3e38441a1b9503e4d9fe2d685edba14c7ec7fdd8bdc2aa77378b358dfb629337"
#blockhash = "6d424c350729ae633275d51dc3496e16cd1b1d195c164da00f39c499a2e9959e" # genesis block

c = 0
tolerance = 10
tc = 0
while True:
	c += 1
	print("* processing {}: {}".format(c,blockhash))
	fp = OUTPUT_DIR + blockhash
	try:
		blk = Block.fromBlockHash(blockhash)
		print("done, block height {}, {} transactions".format(
					blk.coinbase.inputs[0].height,
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

	blk.serialize(fp)
	if blk.coinbase.inputs[0].height == 0:
		break

	blockhash = blk.header.prevBlockHash

print("PASSED ALL TEST CASES")
