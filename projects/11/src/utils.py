
def expect_assert(expect, got):
	if isinstance(expect, list):
		assert got in expect, f"Expect: {' | '.join(expect)}. Got: {got}"
	else:
		assert got == expect, f"Expect: {expect}. Got: {got}"

def append_node(root, child):
	return root.append(child)

