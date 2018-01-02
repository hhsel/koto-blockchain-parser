from .Utility import *
from .Exceptions import *

class Transaction:
	def __str__(self):
		s = "************************* TRANSACTION INFO *************************\n"
		ni = len(self.inputs)
		no = len(self.outputs)
		nj = len(self.joinsplits)
		s += "TXID: {}\n".format(self.txid)
		s += "{} INPUTS\n".format(ni)
		s += "{} OUTPUTS\n".format(no)
		s += "{} JOINSPLITS\n".format(nj)
		s += "version: {}\n".format(self.version)

		for i in range(ni):
			s += "\n////// INPUT {}\n".format(i+1)
			s += str(self.inputs[i])
		for i in range(no):
			s += "\n////// OUTPUT {}\n".format(i+1)
			s += str(self.outputs[i])
		for i in range(nj):
			s += "\n////// JOINSPLIT {}\n".format(i+1)
			s += str(self.joinsplits[i][:32]) + "... [total 1802 bytes]"
			s += "\n"

		return s

	def __init__(self):
		pass

	def _parse(self, b, coinbase=False, genesis=False):
		orig = b
		self.inputs = []
		self.outputs = []
		self.joinsplits = []
		self.version				, b = read_byte(b, 4, True)
		self.size = 4

		n, b, rb = read_varint(b, return_bytes=True)
		self.size += rb

		for _ in range(n):
			ti = TransactionInput(coinbase=True, genesis=genesis)
			b, rb = ti._parse(b)
			self.inputs.append(ti)
			self.size += rb

		n, b, rb = read_varint(b, return_bytes=True)
		self.size += rb
		for i in range(n):
			to = TransactionOutput(b)
			b, rb = to._parse(b)
			to.index = i
			self.outputs.append(to)
			self.size += rb

		self.lock_time			, b = read_byte(b, 4, True)
		self.size += 4

		if self.version <= 1:
			rawtr, _ = read_byte_seq(orig, self.size)
			self.txid = convert_rawtransaction_to_txid(rawtr)
			return b

		# joinsplit information is added if and only if version > 1.
		n, b, rb = read_varint(b, return_bytes=True)
		self.size += rb
		for _ in range(n):
			s, b = read_byte(b, 1802)
			self.size += 1802
			self.joinsplits.append(s)

		if len(self.joinsplits) > 0:
			self.joinsplit_pubkey	, b = read_byte(b, 32)
			self.joinsplit_sig		, b = read_byte(b, 64)
			self.size += 32 + 64

		rawtr, _ = read_byte_seq(orig, self.size)
		self.txid = convert_rawtransaction_to_txid(rawtr)

		return b

class TransactionInput:
	def __init__(self, coinbase=False, genesis=False):
		# the input of the first transaction in a block is called a coinbase.
		self.coinbase = coinbase
		self.genesis = genesis
		self.rawdata = ""

	def __str__(self):
		s = ""
		s += "previous transaction:\n\t {}\n".format(self.prevhash)
		s += "previous transaction index\n\t {}\n".format( int(self.index,16) )
		s += "script:\n\t {}\n".format(self.script)
		return s

	def _parse(self,b):
		total = 0
		if self.coinbase:
			self.prevhash				, b = read_byte(b, 32)	# null (0x000....)
			total += 32
			self.index					, b = read_byte(b, 4)	# 0xffffffff
			total += 4
			self.script_bytes		, b, rb = read_varint(b, return_bytes=True)
			total += rb
			if self.genesis:
				# usual transaction has "[1-byte readout direction][block height]"
				# but the genesis block has a weird lengthy script... just skip those bytes and make height 0.
				# for Koto, it starts with 0x25(meaning script length is 37bytes) 0x04 (read 4 bytes) ....
				self.script					, b = read_byte_seq(b, self.script_bytes)
				total += self.script_bytes
				self.sequence				, b = read_byte(b, 4, True)
				total += 4
				self.height_bytes				= 1
				self.height						= 0
			else:
				# height is only in coinbases. height is a script itself.
				self.height_bytes			, b = read_byte(b, 1, True)
				total += 1

				if 81 <= self.height_bytes and self.height_bytes <= 96:
					# special operation OP1-16
					self.height = self.height_bytes - 80
					self.height_bytes = 0
				elif self.height_bytes == 0:
					self.height_bytes = 0
					self.height = 0
				else:
					self.height				, b = read_byte(b, self.height_bytes, True)
					total += self.height_bytes

				readout_length				= self.script_bytes - self.height_bytes - 1 # 1 for height_bytes, which should be 1-byte readout
				self.script					, b = read_byte_seq(b, readout_length)
				total += readout_length
				self.sequence				, b = read_byte(b, 4, True)

				total += 4
		else:
			self.prevhash				, b = read_byte(b, 32)
			self.index					, b = read_byte(b, 4)
			self.script_bytes		, b, rb = read_varint(b, return_bytes=True)
			self.script					, b = read_byte_seq(b, self.script_bytes)
			self.sequence				, b = read_byte(b, 4, True)

			total += 32+4+rb+self.script_bytes+4

		return b, total

class TransactionOutput:
	def __str__(self):
		s = "value:\n\t {}\n".format(decode_satoshi(self.value))
		s += "script(decoded):\n\t {}\n".format(self.script)
		s += "address:\n\t {}\n".format(self.script.address)
		return s

	def _parse(self,b):
		total = 0

		self.value			, b 	= read_byte(b, 8, True)
		self.pk_script_size	, b, rb = read_varint(b, return_bytes=True)
		script				, b		= read_byte_seq(b, self.pk_script_size)
		self.script					= Script(script)

		total += 8 + rb + self.pk_script_size

		return b, total

	def __init__(self, rawdata):
		self.rawdata = rawdata

class Script:
	def __str__(self):
		return self.script

	def _decode_opcode(self, b):
		op, b = read_byte_seq(b, 1)
		r = None

		nop = int(op,16)

		# push specified bytes (1-75) to the stack
		if 1 <= nop and nop <= 75: # 0x01 - 0x4b
			# * is there some exception that output scripts contain PUSH operations?
			# for example: blockhash = "793e15fd4f18099efb86ccf350851e1a3f88fa25fd865f830c61e958128bafce"
			# contains PUSH 11 before normal routine "0x88ac"
			r = "PUSH[{}]".format(nop)
			if len(b) >= nop:
				t, b = read_byte_seq(b, nop)
		elif 82 <= nop and nop <= 96: # 0x52-0x60
			r = "OP_{}".format(nop-80)
		elif nop == 118:
			r = "OP_DUP"
		elif nop == 101:
			r = "OP_VERIF"
		elif nop == 136:
			r = "OP_EQUALVERIFY"
		elif nop == 157: #0x9d
			r = "OP_NUMEQUALVERIFY"
		elif nop == 166: # 166 = OP_RIPEMD160(0xa6)
			r = "OP_RIPEMD160"
		elif nop == 169:
			# note that the one on Zcash specification is 0x1cbd.
			# the prefix 0x1836 intentionally guarantee the resultant address starts from "k1" or "jz"
			version_prefix = "1836"

			t, b = read_byte_seq(b, 1, True) # this should be 20
			t, b = read_byte_seq(b, t) # 160-bit hash160
			r = "OP_HASH160[{}]".format(t)
			h = t
			h = version_prefix + h
			h = hashlib.sha256( bytes.fromhex(h) ).hexdigest()
			# although the Zcash specification specifies we use ripemd160(sha256(x)), it does not work.
			# sha256(sha256(x)) yields the same address as Koto GUI Wallet and koto-cli.
			h = hashlib.sha256( bytes.fromhex(h) ).hexdigest()
			f = h[:8]
			h = version_prefix + t + f
			h = base58.b58encode( bytes.fromhex(h) )
			self.address = h
		elif nop == 172:
			r = "OP_CHECKSIG"
		elif 179 <= nop and nop <= 185:
			r = "OP_NOP{}".format(nop-179 + 4)
		elif nop == 187:
			# what is 0xbb found on e574d8fc0a69205757759ae67d2ccbfb015b3776629b6ce2638fb27aef193129 ??
			# 0x14 [20bytes of hash] "0xbb" 0x88 0xac [END]
			r = "0xbb?"
		elif nop == 227: # what is 0xe3?
			r = "0xe3?"
		elif nop == 253:
			# 253-255 are invalid
			r = "OP_PUBKEYHASH"

		if r is None:
			raise UnknownOperationCodeException(op)

		return r, b

	def _parse(self):
		s = ""
		b = self.rawdata

		for _ in range(5):
			r, b = self._decode_opcode(b)
			s += r + " "
			if len(b) == 0:
				break

		if len(b) > 0:
			raise IncorrectResultException("there is bytes to be processed in the script field")
		self.script = s[:-1]

	def __init__(self,script):
		self.rawdata = script
		self.address = None
		self._parse()
