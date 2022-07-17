from enum import Enum

class TokenType(Enum):
	KEYWORD = 'keyword'
	SYMBOL = 'symbol'
	IDENTIFIER = 'identifier'
	INT_CONST = 'integerConstant'
	STRING_CONST = 'stringConstant'

token_map = {
		'class': TokenType.KEYWORD,
		'constructor': TokenType.KEYWORD,
		'function': TokenType.KEYWORD,
		'method': TokenType.KEYWORD,
		'field': TokenType.KEYWORD,
		'static': TokenType.KEYWORD,
		'var': TokenType.KEYWORD,
		'int': TokenType.KEYWORD,
		'char': TokenType.KEYWORD,
		'boolean': TokenType.KEYWORD,
		'void': TokenType.KEYWORD,
		'true': TokenType.KEYWORD,
		'false': TokenType.KEYWORD,
		'null': TokenType.KEYWORD,
		'this': TokenType.KEYWORD,
		'let': TokenType.KEYWORD,
		'do': TokenType.KEYWORD,
		'if': TokenType.KEYWORD,
		'else': TokenType.KEYWORD,
		'while': TokenType.KEYWORD,
		'return': TokenType.KEYWORD,
		'{': TokenType.SYMBOL,
		'}': TokenType.SYMBOL,
		'(': TokenType.SYMBOL,
		')': TokenType.SYMBOL,
		'[': TokenType.SYMBOL,
		']': TokenType.SYMBOL,
		'.': TokenType.SYMBOL,
		',': TokenType.SYMBOL,
		';': TokenType.SYMBOL,
		'+': TokenType.SYMBOL,
		'-': TokenType.SYMBOL,
		'*': TokenType.SYMBOL,
		'/': TokenType.SYMBOL,
		'&': TokenType.SYMBOL,
		'|': TokenType.SYMBOL,
		'<': TokenType.SYMBOL,
		'>': TokenType.SYMBOL,
		'=': TokenType.SYMBOL,
		'~': TokenType.SYMBOL
		}

class Tokenizer:
	def __init__(self, path):
		self.path = path
		with open(path) as f: self.lines= f.read().strip().split("\n")
		self.removeComments()
		self.source = " ".join(self.lines)
		self.isource = 0
		self.itokens = 0
		self.tokens = []
		self._token = ""
		self._token_type = None
		self.gen()

	def removeComments(self):
		to_remove = []
		multi_comment = False
		for i in range(len(self.lines)):
			line = self.lines[i].strip()

			multi_comment = ("/*" in line and "*/" not in line) or multi_comment

			if multi_comment:
				multi_comment = not "*/" in line
				to_remove.append(i)
				continue
							
			if line.startswith("//"):
				to_remove.append(i)
				continue

			# in case comment is at starts of the th eline then line.index("//") result in 0
			if "//" in line:
				comment_index = line.index("//")
				comment_index = comment_index - 1 if comment_index != 0 else 0
				line = line[:comment_index]

			# case when one line contain multiple comments
			if "*/" in line:
				comment_index = line.index("/*")
				comment_index = comment_index - 1 if comment_index != 0 else 0
				line = line[:comment_index]
				multi_comment = False

			line = line.strip()
			if len(line) == 0:
				to_remove.append(i)
				continue
			self.lines[i] = line.strip()

		for i in sorted(to_remove, reverse = True):
			del self.lines[i]

		return self.lines

	def hasMoreChars(self)->bool:
		return self.isource < len(self.source)

	def hasMoreTokens(self):
		return self.itokens < len(self.tokens)

	def gen(self):
		self.reset()
		while self.hasMoreChars():
			self.step()
			self.tokens.append({'token':self._token, 'type': self._token_type})
	
	def advance(self):
		self._token = self.tokens[self.itoken]['token']
		self._token_type = self.tokens[self.itoken]['type']
		self.itoken += 1
	
	def back(self):
		self.itoken -= 1
		self._token = self.tokens[self.itoken]['token']
		self._token_type = self.tokens[self.itoken]['type']

	def step(self):
		
		c = self.source[self.isource]
		if c == " ":
			self.isource += 1
			self.step()
			return

		token_type = token_map.get(c, None)
		if token_type == TokenType.SYMBOL:
			self._token = self.source[self.isource]
			self.isource += 1
			self._token_type = TokenType.SYMBOL
			return

		text = ""
		if c == '"':
			while True:
				text += self.source[self.isource]
				self.isource += 1
				if self.source[self.isource] == '"': # look ahead and check if is end of string
					self.isource += 1
					self._token = text[1:]
					self._token_type = TokenType.STRING_CONST
					return
					
		while True:
			c = self.source[self.isource]
			if c == " " or token_map.get(c, None) == TokenType.SYMBOL:
				break
			text += c
			self.isource+=1
		self._token = text
		if text.isnumeric():
			self._token_type = TokenType.INT_CONST
		elif token_map.get(text) == TokenType.KEYWORD:
			self._token_type = TokenType.KEYWORD
		else: 
			self._token_type = TokenType.IDENTIFIER

	def tokenType(self):
		return self._token_type

	def token(self):
		return self._token

	def reset(self):
		self.isource = 0
		self.itoken = 0

