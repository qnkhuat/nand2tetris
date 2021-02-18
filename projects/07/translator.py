import sys
import enum
from pprint import pprint

class CT(enum.Enum):
	C_ARITHMETIC = 1
	C_PUSH = 2
	C_POP = 3
	C_LABLE = 4
	C_GOTO = 5
	C_IF = 6
	C_FUNCTION = 7
	C_RETURN = 8
	C_CALL = 9

class Parser():
	def __init__(self, path):
		with open(path) as f: self.lines = f.read().strip().split("\n")
		self.icommand = 0
		self._arg1 = None
		self._arg2 = None
		self._command_type = None

	def advance(self):
		assert self.icommand < len(self.lines), "Out of command"
		self.command = self.lines[self.icommand].strip()
		self.icommand += 1
		if self.command.strip().startswith('//') or len(self.command) == 0:
			self.advance()
			return
		if "//" in self.command:
			self.command = self.command[:self.command.index('//')].strip()

		#print(f"Process command: {self.command}")
		self._arg_splits = self.command.split(" ")
		
		self._command_type = self.getCommandType(self.arg1())
		#print(f"Command: {self.command}, Type: {self.commandType()}, arg1: {self.arg1()}, arg2: {self.arg2()}, arg3: {self.arg3()}")
		
	def getCommandType(self, arg):
		if arg in ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]:
			return CT.C_ARITHMETIC
		elif arg == "push":
			return CT.C_PUSH
		elif arg == "pop":
			return CT.C_POP
		elif arg == "goto":
			return CT.C_GOTO
		elif arg == "if":
			return CT.C_IF
		elif arg == "function":
			return CT.FUCNTION
		elif arg == "return":
			return CT.RETURN
		elif arg == "label":
			return CT.C_LABEL
		raise ValueError(f"Invalid command type: {arg}")

	def args(self):
		return self._arg_splits

	def arg1(self): 
		assert self.commandType() != CT.C_RETURN, "Not allowed to call for C_RETURN command"
		return self._arg_splits[0]

	def arg2(self): 
		#assert self.commandType() in [CT.C_PUSH, CT.C_POP, CT.C_FUNCTION, CT.C_CALL], "Not allowed to call arg2"
		return self._arg_splits[1] if len(self._arg_splits) > 1 else None

	def arg3(self): 
		#assert self.commandType() in [CT.C_PUSH, CT.C_POP]
		return self._arg_splits[2] if len(self._arg_splits) > 2 else None

	def hasMoreCommands(self):
		return self.icommand < len(self.lines)

	def commandType(self):
		return self._command_type
	
	def reset(self):
		self.icommand = 0
	

class Translator():
	def __init__(self, path, verbose=True):
		self.p = Parser(path)
		self.asms = []
		self.verbose = verbose
		self._ilabel = 0
		self._fname = path.split("/")[-1].split(".")[0]
	
	def add(self, command):
		self.asms.append(command)
	
	def add_c(self, comment):
		if self.verbose:
			self.asms.append(f"// {comment}")

	def get_l(self, label):
		label = f"{label}{self._ilabel}"
		self._ilabel +=1
		return label

	def _inc_sp(self):
		self.add("@SP")
		self.add("M=M+1")

	def _dec_sp(self):
		self.add("@SP")
		self.add("M=M-1")

	def _getv2D(self, addr):
		# get value from pointer
		self.add(addr)
		self.add("A=M")
		self.add("D=M")
		
	def _lstack2D(self):
		self.add("@SP")
		self.add("A=M-1")
		self.add("D=M")

	def _pushd(self, addr="@SP"):
		self.add(addr)
		self.add("A=M")
		self.add("M=D")

	def _compare(self, op):
		self.gen_a("sub")
		self.add("@SP")
		self.add("A=M-1")
		self.add("D=M")
		false = self.get_l("FALSE")
		cont = self.get_l("CONTINUE")
		self.add(f"@{false}")
		self.add(f"D;{op}") # jump to false
		self.add("@SP") # if True
		self.add("A=M-1")
		self.add("M=0") # set as false
		self.add(f"@{cont}")
		self.add("0;JMP")
		self.add(f"({false})")
		self.add("@SP")
		self.add("A=M-1")
		self.add("M=-1") # set as true
		self.add(f"({cont})")
	
	def _binary(self, op):
		assert op in ['|', '&', '+', '-'], "Invalid opreration"
		self.add("@SP")
		self.add("AM=M-1")
		self.add("D=M")
		self.add("A=A-1")
		self.add(f"M=M{op}D")

	def _unary(self, op):
		assert op in ['-', '!'], "Invalid opreration"
		self.add("@SP")
		self.add("A=M-1")
		self.add(f"M={op}M")

	def gen_a(self, command):
		""" Gen arithmetic command """
		if command == "add":
			self._binary('+')
		elif command == "sub":
			self._binary('-')
		elif command == "and":
			self._binary('&')
		elif command == "or":
			self._binary('|')
		elif command == 'eq':
			self._compare('JEQ')
		elif command == 'gt':
			self._compare('JGT')
		elif command == 'lt':
			self._compare('JLT')
		elif command == "neg":
			self._unary('-')
			self.add("@SP")
		elif command == "not":
			self._unary('!')
		else:
			raise ValueError("Operation not supported")

	def gen_p(self, command, segment, index):
		""" Gen push/pop command """
		if command == "push":
			# Push the value of segment[index] onto the stack
			if segment == "constant":
				self.add(f"@{index}")
				self.add("D=A")
				self._pushd()
				self._inc_sp()
			elif segment == "pointer":
				if int(index) == 0:
					self.add("@THIS")
				elif int(index) == 1:
					self.add("@THAT")
				self.add("D=M")
				self._pushd()
				self._inc_sp()
			else:
				# get the value of segment and store it to R5
				if segment == "local":
					self.add("@LCL")
					self.add("D=M")				
				elif segment == "argument":
					self.add("@ARG")
					self.add("D=M")				
				elif segment == "this" or (segment == "pointer" and int(index) == 0):
					self.add("@THIS")
					self.add("D=M")				
				elif segment == "that" or (segment == "pointer" and int(index) == 1):
					self.add("@THAT")
					self.add("D=M")				
				elif segment == "temp":
					self.add("@R5")
					self.add("D=A")				
				elif segment == "static":
					self.add(f"@{16+int(index)}")
					self.add("D=A")
				else: raise ValueError("Operation not supported") 
				self.add(f"@{index}")
				self.add("A=D+A") 
				self.add("D=M") # value of segment now is in D

				# store it in stack
				self._pushd()
				self._inc_sp()

		elif command == 'pop':
			# get address to store value
			if segment == "pointer":
				self._dec_sp()
				self._pushd()
				if int(index) == 0:
					self.add("@THIS")
				elif int(index) == 1:
					self.add("@THAT")
				self.add("M=D")
			else:
				# Pop the top stack value and store it in segment[index]
				self._lstack2D()
				self.add("@R5")
				self.add("M=D") # store the value from stack at R5
				if segment == "local":
					self.add("@LCL")
					self.add("D=M")
				elif segment == "argument":
					self.add("@ARG")
					self.add("D=M")
				elif segment == "this":
					self.add("@THIS")
					self.add("D=M")
				elif segment == "that":
					self.add("@THAT")
					self.add("D=M")
				elif segment == "temp":
					self.add(f"@R5")
					self.add("D=A")
				elif segment == "static":
					self.add(f"@{16+int(index)}")
					self.add("D=A")
				else: raise ValueError("Operation not supported") 
				self.add(f"@{index}")
				self.add("D=D+A")
				# store the address to a temp
				self.add("@R6")
				self.add("M=D")

				# fill value into address
				self.add("@R5") # get value
				self.add("D=M")
				self._pushd("@R6")
				self._dec_sp()

		else:
			raise ValueError("Operation not supported")


	def reset(self):
		self.asms = []

	def gen(self):
		self.p.reset()
		while self.p.hasMoreCommands():
			self.p.advance()
			if self.verbose:
				print(f"Command: {self.p.command}, Type: {self.p.commandType()}, arg1: {self.p.arg1()}, arg2: {self.p.arg2()}, arg3: {self.p.arg3()}")
			self.add_c(self.p.command)
			if self.p.commandType() == CT.C_ARITHMETIC:
				self.gen_a(self.p.arg1())
			elif self.p.commandType() in [CT.C_PUSH, CT.C_POP]:
				self.gen_p(self.p.arg1(), self.p.arg2(), self.p.arg3())

		if self.verbose:
			pprint(self.asms)

	def write(self, path):
		with open(path, "w") as f:
			f.writelines([f"{line}\n" for line in self.asms])

if __name__ == "__main__":
	filename = sys.argv[1]
	outfile = filename.replace(".vm", ".asm")
	print(f"Parsing file {filename}")
	t = Translator(filename, verbose=False)
	t.gen()
	t.write(outfile)
	print(f"Wrote to {outfile}")


