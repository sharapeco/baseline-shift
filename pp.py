from ppretty import ppretty

def pp(value: any, seq_length: int = 50, depth: int = 5) -> str:
	return ppretty(value, seq_length=seq_length, depth=depth)