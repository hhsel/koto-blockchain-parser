import hashlib
import base58
from . import RPCHelper

class RunOutOfStringException(Exception): pass
class IncorrectResultException(Exception): pass
class UnknownOperationCodeException(Exception): pass
class RPCErrorException(Exception): pass

# read bytes in the little endian manner.
def read_byte(s,n, convert_int=False):
	if n*2 > len(s):
		raise RunOutOfStringException()
	r = ""
	for i in range(n):
		r += s[(n-i-1)*2:(n-i)*2]

	if convert_int:
		r = int(r,16)

	return r, s[n*2:]
# read bytes from input string sequentially.
def read_byte_seq(s,n, convert_int=False):
	if n*2 > len(s):
		raise RunOutOfStringException()
	r = s[:n*2]

	if convert_int:
		r = int(r,16)

	return r, s[n*2:]
# decode variable integer. note that varint (VI) is not the "variable-length integer" you might expect when you first hear it.
# it just regard input as multibyte if that exceeds 252, rendering 253, 254, and 255 control signals.
def read_varint(s):
	n, s = read_byte(s, 1, True)

	if n <= 252:
		pass
	elif n == 253:
		n, s = read_byte(s, 2, True)
	elif n == 254:
		n, s = read_byte(s, 5, True)
	else: # ( n == 255 )
		n, s = read_byte(s, 7, True)
	return n, s

def diff(s):
	header, _ = read_byte(s, 80)
	d = hashlib.sha256( hashlib.sha256(header) )
	return d
def decode_satoshi(a):
	return a / 100000000

class Transaction:
	def __str__(self):
		s = "************************* TRANSACTION INFO *************************\n"
		ni = len(self.inputs)
		no = len(self.outputs)
		nj = len(self.joinsplits)
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
			s += str(self.joinsplits[i][:32])

		return s
class TransactionInput:
	def __str__(self):
		s = ""
		s += "previous transaction:\n\t {}\n".format(self.previous_transaction)
		s += "script(sig + pubkey):\n\t {}\n".format(self.script)
		return s

	def _parse(self,b):
		self.previous_transaction	, b = read_byte(b, 32)
		self.previous_txout_index	, b = read_byte(b, 4)
		self.script_length			, b = read_varint(b)
		self.script_height_length	, b = read_varint(b)
		self.script_height			, b = read_byte(b, self.script_height_length, True)
		j = len(hex(self.script_length)[2:]) # if the value is 1, it will get 0. we need to augument it to 2 when it's 1
		if j == 1: j = 2
		readout_length				= self.script_length - self.script_height_length - j // 2
		script						, b = read_byte_seq(b, readout_length)
		self.script					= script #Script(script)
		self.sequence				, b = read_byte(b, 4, True) # Default for Bitcoin Core and almost all other programs is 0xffffffff.
		return b

class TransactionOutput:
	def __str__(self):
		s = "value:\n\t {}\n".format(decode_satoshi(self.value))
		s += "script(decoded):\n\t {}\n".format(self.script)
		s += "address:\n\t {}\n".format(self.script.address)
		return s

	def _parse(self,b):
		self.value			, b = read_byte(b, 8, True)
		self.pk_script_size	, b = read_varint(b)
		script				, b	= read_byte_seq(b, self.pk_script_size)
		self.script			= Script(script, self.sig_pubkey)
		return b

	def __init__(self, rawdata):
		self.rawdata = rawdata
		self.sig_pubkey = None

class Script:
	def __str__(self):
		return self.script

	def _decode_opcode(self, b):
		op, b = read_byte_seq(b, 1)
		r = None

		nop = int(op,16)

		# push specified bytes (1-75) to the stack
		if 1 <= nop and nop <= 75:
			t, b = read_byte_seq(b, nop)
			r = "PUSH[{}]".format(nop)
		elif nop == 118:
			r = "OP_DUP"
		elif nop == 101:
			r = "OP_VERIF"
		elif nop == 136:
			r = "OP_EQUALVERIFY"
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

	def __init__(self,script,sig_pubkey=None):
		self.rawdata = script
		self._parse()

class Block:
	def _parseBlockHeader(self, b):
		class BlockHeader: pass
		bh = BlockHeader()
		bh.version			, b = read_byte(b, 4, True)
		bh.prevBlockHash	, b = read_byte(b, 32)
		bh.MerkleRoot		, b = read_byte(b, 32)
		bh.nTime			, b = read_byte(b, 4, True)
		bh.nBits			, b = read_byte(b, 4, True)
		bh.nNonce			, b = read_byte(b, 4, True)
		return bh, b

	def _parseTransaction(self, b, coinbase=False):
		#if coinbase == False: print(b)
		t = Transaction()
		t.inputs = []
		t.outputs = []
		t.joinsplits = []
		t.version				, b = read_byte(b, 4, True)

		n, b = read_varint(b)
		for _ in range(n):
			ti = TransactionInput()
			b = ti._parse(b)
			sig_pubkey = ti.script
			t.inputs.append(ti)

		n, b = read_varint(b)
		for _ in range(n):
			to = TransactionOutput(b)
			b = to._parse(b)
			t.outputs.append(to)

		t.lock_time			, b = read_byte(b, 4, True)

		if t.version <= 1:
			return t, b

		# joinsplit information is added if and only if version > 1.
		n, b = read_varint(b)
		for _ in range(n):
			s, b = read_byte(b, 1802)
			t.joinsplits.append(s)

		if len(t.joinsplits) > 0:
			t.joinsplit_pubkey	, b = read_byte(b, 32)
			t.joinsplit_sig		, b = read_byte(b, 64)

		return t, b

	def _parseBlock(self):
		self.header, remainder = self._parseBlockHeader(self.rawdata)

		n,remainder = read_varint(remainder)
		self.transactions = []

		# the first transation is the coinbase transaction in a block
		tr, remainder = self._parseTransaction(remainder, coinbase=True)
		self.coinbase = tr
		n = n - 1

		for i in range(n):
			tr, remainder = self._parseTransaction(remainder)
			self.transactions.append(tr)

		if(len(remainder)):
			raise IncorrectResultException("there are some bits not processed:\n{}".format(remainder))

	def __init__(self, rawdata):
		self.rawdata = rawdata
		self._parseBlock()

	def __str__(self):
		s = str(self.coinbase)

		for i in range(len(self.transactions)):
			s += str(self.transactions[i])
		return s

	@staticmethod
	def fromRawData(rawdata):
		return __class__(rawdata)
	@staticmethod
	def fromBlockHash(blockhash):
		try:
			rawdata = RPCHelper.get_rawblockdata(blockhash)
		except Exception:
			raise RPCErrorException("failed to connect to the server. this is a HTTP error.")
		return __class__(rawdata)
