table = {
	0x5C: '¥',
	0x80: '\\',
	0xA0: ' ',
	0xFD: '©',
	0xFE: '™',
	0xFF: '…',
}

def decode(data: bytes) -> str:
	str = ''
	pos = 0
	length = len(data)
	while pos < length:
		firstByte = data[pos]
		if firstByte in table.keys():
			str += table[firstByte]
			pos += 1
		elif firstByte >= 0x81:
			str += data[pos:pos+2].decode('Shift_JIS')
			pos += 2
		else:
			str += data[pos:pos+1].decode('Shift_JIS')
			pos += 1
	return str
