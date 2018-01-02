import hashlib
import base58

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
def read_varint(s, return_bytes = False):
	total = 0
	n, s = read_byte(s, 1, True)
	total += 1

	if n <= 252:
		pass
	elif n == 253:
		n, s = read_byte(s, 2, True)
		total += 2
	elif n == 254:
		n, s = read_byte(s, 4, True)
		total += 4
	else: # ( n == 255 )
		n, s = read_byte(s, 8, True)
		total += 8
	if return_bytes == True:
		return n,s,total
	return n, s
def convert_rawtransaction_to_txid(rawtr):
	h = hashlib.sha256( bytes.fromhex(rawtr) ).hexdigest()
	h = hashlib.sha256( bytes.fromhex(h) ).digest()
	txid = bytes.hex(h[::-1])
	return txid

def diff(s):
	header, _ = read_byte(s, 80)
	d = hashlib.sha256( hashlib.sha256(header) )
	return d
def decode_satoshi(a):
	return a / 100000000
