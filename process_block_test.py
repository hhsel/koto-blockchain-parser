from KotoBlockchainParser import Block

with open("testcase.txt","r") as f:
	ls = f.read().split("\n")[:-1]
	ls = [s[29:] for s in ls]

for blockhash in ls:
	print("processing {}".format(blockhash))

	blk = Block.fromBlockHash(blockhash)
	print(blk)

print("PASSED ALL TEST CASES")
