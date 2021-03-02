import xml.etree.ElementTree as ET
from tokenizer import Tokenizer, TokenType
from utils import *


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
				

