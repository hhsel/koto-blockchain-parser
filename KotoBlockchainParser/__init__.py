import hashlib
from . import RPCHelper
from .Transaction import Transaction
from .Utility import *
from .Exceptions import *
import pickle

class BlockHeader:
	def __str__(self):
		s = "************************* BLOCK HEADER *************************\n"
		s += "prev. hash: {}".format(self.prevBlockHash)
		s += "\nbits: {}\n".format(self.nBits)
		s += "\ndifficulty: {}\n".format(self.difficulty)
		return s

class Block:
	blockhash = None

	def _parseBlockHeader(self, b):
		bh = BlockHeader()
		bh.version			, b = read_byte(b, 4, True)
		bh.prevBlockHash	, b = read_byte(b, 32)
		bh.MerkleRoot		, b = read_byte(b, 32)
		bh.nTime			, b = read_byte(b, 4, True)
		bh.nBits			, b = read_byte(b, 4)
		bh.nNonce			, b = read_byte(b, 4, True)
		d = lambda x: int(x[2:], 16) * (2**(8*(int(x[:2], 16) - 3)))
		bh.difficulty			= d("1d00ffff") / d(bh.nBits)

		if int(bh.prevBlockHash,16) == 0:
			self.genesis = True
		return bh, b

	def _parseBlock(self):
		self.header, remainder = self._parseBlockHeader(self.rawdata)

		n,remainder = read_varint(remainder)
		self.transactions = []

		# the first transation is the coinbase transaction in a block
		tr = Transaction()
		remainder = tr._parse(remainder, coinbase=True, genesis=self.genesis)
		self.coinbase = tr
		n = n - 1

		for i in range(n):
			tr = Transaction()
			remainder = tr._parse(remainder, genesis=self.genesis)
			self.transactions.append(tr)

		if(len(remainder)):
			raise IncorrectResultException("there are some bits not processed:\n{}".format(remainder))

	def __init__(self, rawdata):
		self.rawdata = rawdata
		self.genesis = False
		self._parseBlock()

	def __str__(self):
		s = self.blockhash + "\n"
		s += str(self.header)
		s += str(self.coinbase)

		for i in range(len(self.transactions)):
			s += str(self.transactions[i])
		return s

	def serialize(self,output):
		with open(output, "wb") as f:
			pickle.dump(self, f)

	@staticmethod
	def fromRawData(rawdata):
		return __class__(rawdata)
	@staticmethod
	def fromBlockHash(blockhash):
		try:
			rawdata = RPCHelper.get_rawblockdata(blockhash)
		except Exception:
			raise RPCErrorException("failed to connect to the server. this is a HTTP error.")

		c = __class__(rawdata)
		c.blockhash = blockhash
		return c
