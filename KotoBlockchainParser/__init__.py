import hashlib

class RunOutOfStringException(Exception): pass
class IncorrectResultException(Exception): pass

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
		s += "script:\n\t {}\n".format(self.script)
		s += "sequence:\n\t {}\n".format(self.sequence)
		return s
class TransactionOutput:
	def __str__(self):
		s = "value:\n\t {}\n".format(decode_satoshi(self.value))
		s += "script:\n\t {}\n".format(self.pk_script)
		return s
class KotoBlock:
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
			ti.previous_transaction	, b = read_byte(b, 32)
			ti.previous_txout_index	, b = read_byte(b, 4)
			ti.script_length		, b = read_varint(b)
			ti.script_height_length	, b = read_varint(b)
			ti.script_height		, b = read_byte(b, ti.script_height_length, True)
			j = len(hex(ti.script_length)[2:])
			if j == 1: j = 2
			readout_length				= ti.script_length - ti.script_height_length - j // 2
			ti.script				, b = read_byte_seq(b, readout_length)
			ti.sequence				, b = read_byte(b, 4, True) # Default for Bitcoin Core and almost all other programs is 0xffffffff.
			t.inputs.append(ti)

		n, b = read_varint(b)
		for _ in range(n):
			to = TransactionOutput()
			to.value			, b = read_byte(b, 8, True)
			to.pk_script_size	, b = read_varint(b)
			to.pk_script		, b = read_byte_seq(b, to.pk_script_size)
			t.outputs.append(to)

		t.lock_time			, b = read_byte(b, 4, True)

		if t.version <= 1:
			return t, b


		# joinsplit information is added if and only if version > 1.
		#t.dummy			, b = read_byte(b, 4, True)
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

	def __init__(self, rawblock):
		self.rawdata = rawblock
		self._parseBlock()

	def __str__(self):
		s = str(self.coinbase)

		for i in range(len(self.transactions)):
			s += str(self.transactions[i])
		return s
