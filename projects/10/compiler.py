from lxml import etree
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys, os, glob
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

def expect_assert(expect, got):
	if isinstance(expect, list):
		assert got in expect, f"Expect: {' | '.join(expect)}. Got: {got}"
	else:
		assert got == expect, f"Expect: {expect}. Got: {got}"

def append_node(root, child):
	return root.append(child)
	
class CompilationEngine:
	def __init__(self, path):
		self.t = Tokenizer(path)
		self._class_var_types = ['static', 'field']
		self._types = ['int', 'char', 'boolean', 'void']
		self._subroutine_types = ['constructor', 'function', 'method']
		self._statement_types = ["let", "if", "else", "while", "do", "return"]
		self._ops = ['+', '-', '*', '/', '&', '|', '<', '>', '=']
		self._unaryOps = ['-', '~']
		self._constatns = ['true', 'false', 'null', 'this']
	
	def new_node(self, key, value="\n"):
		node = ET.Element(key)
		node.tail = "\n"
		node.text = value 
		return node

	def compileClass(self):
		root = self.new_node('class')
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # class

		self.t.advance() # eat class_name
		class_name = self.t.token()
		append_node(root, self.new_node(self.t.tokenType().value, class_name))
		self.t.advance()

		expect_assert("{", self.t.token()) # eat open
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		while True:
			self.t.advance()
			if self.t.token() == "}":
				break
			if self.t.token() in self._class_var_types:
				append_node(root, self.compileClassVarDec())
			elif self.t.token() in self._subroutine_types:
				append_node(root, self.compileSubroutine())
			
		expect_assert('}', self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # }
		return root

	def compileClassVarDec(self):
		root = self.new_node('classVarDec')
		expect_assert(self._class_var_types, self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance() # type
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		while True:
			self.t.advance()
			if self.t.token() == ';':
				append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
				break
			elif self.t.token() == ',':
				append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
				continue
			expect_assert(TokenType.IDENTIFIER, self.t.tokenType())
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		return root

	def compileSubroutine(self):
		# ('constructor'|'function'|'method')('void'|type) subroutineName (parameterList)
		# call compile ParameterList
		# varDec* statements
		root = self.new_node('subroutineDec')
		expect_assert(self._subroutine_types, self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # routine type

		self.t.advance() # return type
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) 

		self.t.advance() # subroutine name
		expect_assert(TokenType.IDENTIFIER, self.t.tokenType())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance() # eat open
		expect_assert("(", self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		append_node(root, self.compileParameterList())

		expect_assert(")", self.t.token()) # eat close
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
		
		# body
		append_node(root, self.compileSubroutineBody())
		
		return root

	def compileSubroutineBody(self):
		root = self.new_node("subroutineBody")

		self.t.advance() # eat open
		expect_assert("{", self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		is_statements = False
		while True:
			self.t.advance()
			if self.t.token() == "}":
				break

			if self.t.token() == "var":
				append_node(root, self.compileVarDec())
				assert not is_statements, "Var must defined before Statements"
			else:
				is_statements = True
				append_node(root, self.compileStatements())
				
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # eat close
		return root


	def compileParameterList(self):
		# type VarName, (type varName)*
		root = self.new_node('parameterList')
		while True:
			self.t.advance()
			if self.t.token() == ")":
				return root
			#expect_assert(self._types, self.t.token()) # type
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
			
	def compileVarDec(self):
		# var type varName(',' varName)*
		root = self.new_node('varDec')
		expect_assert('var', self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance() # type
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		while True:
			self.t.advance()
			if self.t.token() == ';':
				append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
				break
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		return root

	def compileStatements(self):
		# letStatement | ifStatement | whileStatement | doStatement | returnStatement
		root = self.new_node('statements')
		while True:
			token = self.t.token()
			if self.t.token() == "}":
				self.t.back()
				return root

			#expect_assert(self._statement_types, token)
			if token == 'let':
				append_node(root, self.compileLet())
			elif token == 'if':
				append_node(root, self.compileIf())
			elif token == 'while':
				append_node(root, self.compileWhile())
			elif token == 'do':
				append_node(root, self.compileDo())
			elif token == 'return':
				append_node(root, self.compileReturn())

			self.t.advance()
						
	def compileDo(self):
		root = self.new_node('doStatement')
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # do

		self.t.advance()
		expect_assert(TokenType.IDENTIFIER, self.t.tokenType())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance()
		if self.t.token() == '.': # classname.subroutine
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
			self.t.advance()
			expect_assert(TokenType.IDENTIFIER, self.t.tokenType())
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
			self.t.advance()

		expect_assert("(", self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance()
		append_node(root, self.compileExpressionList())

		expect_assert(")", self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance()
		expect_assert(';', self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
		return root

	def compileLet(self):
		root = self.new_node('letStatement')
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # let
		
		self.t.advance() # var name
		expect_assert(TokenType.IDENTIFIER, self.t.tokenType())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance()
		if self.t.token() == '[': # index
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
			self.t.advance()
			append_node(root, self.compileExpression())
			expect_assert(']', self.t.token())
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
			self.t.advance()

		expect_assert("=", self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
		self.t.advance()
		append_node(root, self.compileExpression())	
		expect_assert(';', self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		return root

	def compileWhile(self):
		root = self.new_node('whileStatement')
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # while

		self.t.advance()
		expect_assert("(", self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance()
		append_node(root, self.compileExpression())
		
		expect_assert(")", self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance()
		expect_assert("{", self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance()
		append_node(root, self.compileStatements())

		self.t.advance()
		expect_assert("}", self.t.token()) # eat close
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		return root

	def compileReturn(self):
		root = self.new_node('returnStatement')
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # return

		self.t.advance()
		if self.t.token() != ';':
			append_node(root, self.compileExpression())
		
		expect_assert(';', self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
		return root

	def compileIf(self):
		root = self.new_node('ifStatement')
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # if

		self.t.advance()
		expect_assert("(", self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance()
		append_node(root, self.compileExpression())
		
		expect_assert(")", self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance()
		expect_assert("{", self.t.token())
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance()
		append_node(root, self.compileStatements())

		self.t.advance()
		expect_assert("}", self.t.token()) # eat close
		append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		self.t.advance()
		if self.t.token() == 'else':
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # if

			self.t.advance()
			expect_assert("{", self.t.token())
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

			self.t.advance()
			append_node(root, self.compileStatements())

			self.t.advance()
			expect_assert("}", self.t.token()) # eat close
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

		else:
			self.t.back()

		return root
	
	def compileExpression(self):
		root = self.new_node('expression')
		append_node(root, self.compileTerm())
		self.t.advance()
		if self.t.token() in self._ops:
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # binary op
			self.t.advance()
			append_node(root, self.compileTerm())
			self.t.advance()
		return root

	def compileTerm(self):
		root = self.new_node('term')
		if self.t.tokenType() == TokenType.IDENTIFIER:
			root.append(self.new_node(self.t.tokenType().value, self.t.token()))
			self.t.advance() # look ahead
			if self.t.token() == '[': # index
				append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) #  [
				self.t.advance()
				append_node(root, self.compileExpression())
				expect_assert(']', self.t.token()) 
				append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
			elif self.t.token() == '.':
				append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # .
				self.t.advance()
				append_node(root, self.new_node('identifier', self.t.token())) # subroutine name
				self.t.advance()

				expect_assert("(", self.t.token()) # (
				append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

				self.t.advance()
				append_node(root, self.compileExpressionList())
				
				expect_assert(")", self.t.token()) # )
				append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

			else:
				self.t.back()

		elif self.t.tokenType() == TokenType.STRING_CONST:
			root.append(self.new_node(self.t.tokenType().value, self.t.token()))
		elif self.t.tokenType() == TokenType.INT_CONST:
			root.append(self.new_node(self.t.tokenType().value, self.t.token()))
		elif self.t.tokenType() == TokenType.KEYWORD:
			root.append(self.new_node(self.t.tokenType().value, self.t.token()))
		elif self.t.token() == '(':
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))

			self.t.advance()
			append_node(root, self.compileExpression())
			
			expect_assert(")", self.t.token())
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token()))
		elif self.t.token() in self._unaryOps:
			append_node(root, self.new_node(self.t.tokenType().value, self.t.token())) # unary operation
			self.t.advance()
			append_node(root, self.compileTerm())
		else:
			raise ValueError(f"What the fuck is this: {self.t.token()}")

		return root


	def compileExpressionList(self):
		root = self.new_node("expressionList")
		while True:
			if self.t.token() == ')':
				return root
			append_node(root, self.compileExpression())
			if self.t.token() == ',':
				root.append(self.new_node(self.t.tokenType().value, self.t.token()))
				self.t.advance()
				

class Analyzer:
	def __init__(self, path):
		self.c = CompilationEngine(path)
	
	def _print(self):
		self.c.t.reset()
		while self.c.t.hasMoreTokens():
			self.c.t.advance()
			print(f"Type : {self.c.t.tokenType()} \t| Key : {self.c.t.token()}")

	def gen(self):
		self.c.t.reset()
		self.c.t.advance()
		expect_assert("class", self.c.t.token())
		root = self.c.compileClass()
		outpath = self.c.t.path.replace(".jack", "Out.xml")
		with open(outpath, "wb") as f :
			f.write(ET.tostring(root, short_empty_elements=False))

		print(f"Wrote to {outpath}")


if __name__ == "__main__":
	verbose = True 
	if len(sys.argv) < 2:
		print("usage: compiler.py {path to .jack file}")
		sys.exit(0)
	path = sys.argv[1]
	if os.path.isdir(path):
		print(f"Compiling folder {path}")
		list_files = [p for p in os.listdir(path) if p.endswith(".jack")]
		for f in list_files:
			print(f"Sub file {f}")
			a = Analyzer(os.path.join(path, f))
			a.gen()
	else:
		print(f"Compiling file {path}")
		a = Analyzer(path)
		a.gen()


