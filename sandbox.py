from KotoBlockchainParser import Block

bh = "5ca97407ecf6b0811b0aa14003d287d094267ab33acb3a205e27b6a70c5ca779"
blk = Block.fromBlockHash(bh)
print(blk)
