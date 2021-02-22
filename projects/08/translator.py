import sys, os
import enum
from pprint import pprint
from glob import glob

class CT(enum.Enum):
	C_ARITHMETIC = 1
	C_PUSH = 2
	C_POP = 3
	C_LABEL = 4
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
		self.irom = 0

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
		self.irom += 1
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
		elif arg == "if-goto":
			return CT.C_IF
		elif arg == "function":
			return CT.C_FUNCTION
		elif arg == "return":
			return CT.C_RETURN
		elif arg == "label":
			return CT.C_LABEL
		elif arg == "call":
			return CT.C_CALL

		raise ValueError(f"Invalid command type: {arg}")

	def args(self):
		return self._arg_splits

	def arg1(self): 

		#assert self.commandType() != CT.C_RETURN, "Not allowed to call for C_RETURN command"
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
		self._static_prefix = path.split("/")[-1].split(".")[0]

	def add(self, command):
		self.asms.append(command)

	def add_c(self, comment):
		# add comment
		if verbose:
			self.asms.append(f"// {comment}")

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

	def _popD(self):
		self.add("@SP")
		self.add("AM=M-1")
		self.add("D=M")

	def _pushD(self, addr="@SP"):
		# push the current value of D register to an address
		self.add('@SP')
		self.add('M=M+1')
		self.add('A=M-1')
		self.add('M=D')

	def _compare(self, op):
		self.gen_arith("sub")
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

	def get_l(self, label):
		# return a distinct label
		label = f"{label}{self._ilabel}"
		self._ilabel +=1
		return label

	def gen_arith(self, command):
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

	def gen_label(self, label):
		# label LABEL 
		self.add(f"({label})")

	def gen_if(self, dest):
		# if-goto DEST
		self._popD()
		self.add(f"@{dest}")
		self.add(f"D;JNE") # jump to false

	def gen_go(self, dest):
		self.add(f"@{dest}")
		self.add("0;JMP")

	def gen_p(self, command, segment, index):
		""" Gen push/pop command """
		if command == "push":
			# Push the value of segment[index] onto the stack
			if segment == "constant":
				self.add(f"@{index}")
				self.add("D=A")
				self._pushD()
			elif segment == "pointer":
				if int(index) == 0:
					self.add("@THIS")
				elif int(index) == 1:
					self.add("@THAT")
				self.add("D=M")
				self._pushD()
			elif segment == "static":
				self.add(f"@{self._static_prefix}.{index}")
				self.add('D=M')
				self._pushD()
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
				else: raise ValueError("Operation not supported") 
				self.add(f"@{index}")
				self.add("A=D+A") 
				self.add("D=M") # value of segment now is in D

				# store it in stack
				self._pushD()
		elif command == 'pop':
			# Move the top stack value to segment[index]
			if segment == "pointer":
				self._popD()
				if int(index) == 0:
					self.add("@THIS")
				elif int(index) == 1:
					self.add("@THAT")
				self.add("M=D")
			elif segment == "temp":
				self._popD()
				self.add(f"@R{5+int(index)}")
				self.add('M=D')
			elif segment == "static":
				self._popD()
				self.add(f"@{self._static_prefix}.{index}")
				self.add('M=D')
			else:
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
				else: raise ValueError("Operation not supported") 
				self.add(f"@{index}")
				self.add("D=D+A")
				self.add("@R13")
				self.add("M=D")
				self._popD()
				self.add("@R13")
				self.add("A=M")
				self.add("M=D") # store the value from stack at R5

		else:
			raise ValueError("Operation not supported")

	def gen_init(self):
		self.add('@256')
		self.add('D=A')
		self.add('@SP')
		self.add('M=D')
		self.add_c('call Sys.init')
		self.gen_call('Sys.init', 0)


	def gen_func(self, func, n):
		# Initialize the local variables of the callee
		# local variables is variables that the function is going to used during computation
		self.gen_label(func)
		self.add("D=0")
		for i in range(int(n)):
			self._pushD()
		# Handle some other simple initializations (later)

	def gen_call(self, func, m):
		# Determine the return address within the caller’s code

		return_addr = self.get_l(f"RETURN_{func}")
		self.add(f"@{return_addr}")
		self.add("D=A")
		self._pushD()

		# Save the caller’s return address, stack and memory segments
		push_list = ["@LCL", "@ARG", "@THIS", "@THAT"]
		for addr in push_list:
			self.add(addr)
			self.add("D=M")
			self._pushD()
	
		# Pass parameters from the caller to the callee
		self.add('@SP') # ARG = SP - m - 5
		self.add('D=M')
		self.add(f"@{int(m) + 5}")
		self.add('D=D-A')
		self.add('@ARG')
		self.add('M=D')

		self.add("@SP") # LCL = SP
		self.add("D=M")
		self.add("@LCL")
		self.add("M=D")


		# Jump to execute the callee
		self.gen_go(func)
		self.gen_label(return_addr)



	def gen_re(self):

		# R13 = LCL
		self.add('@LCL')
		self.add('D=M')
		self.add('@R13')
		self.add('M=D')
		# R14 = *(R13 - 5) (save return address)
		self.add('@5')
		self.add('A=D-A')
		self.add('D=M')
		self.add('@R14')
		self.add('M=D')		
		# Return the return value to the caller
		# *ARG = pop()
		self._popD()
		self.add('@ARG')
		self.add('A=M')
		self.add('M=D')
		# SP = ARG + 1
		self.add('@ARG')
		self.add('D=M+1')
		self.add('@SP')
		self.add('M=D')

		# Recycle the memory resources used by the callee
		push_list = ["@THAT", "@THIS", "@ARG", "@LCL"]
		# Restore THAT, THIS, ARG, LCL
		for addr in push_list:
			self.add('@R13')
			self.add('AM=M-1')
			self.add('D=M')
			self.add(addr)
			self.add('M=D')

		# Jump to the return address in the caller’s code
		# Return (goto R14)
		self.add('@R14')
		self.add('A=M')
		self.add('0;JMP')


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
				self.gen_arith(self.p.arg1())
			elif self.p.commandType() in [CT.C_PUSH, CT.C_POP]:
				self.gen_p(self.p.arg1(), self.p.arg2(), self.p.arg3())
			elif self.p.commandType() == CT.C_LABEL:
				self.gen_label(self.p.arg2())
			elif self.p.commandType() == CT.C_IF:
				self.gen_if(self.p.arg2())
			elif self.p.commandType() == CT.C_GOTO:
				self.gen_go(self.p.arg2())
			elif self.p.commandType() == CT.C_RETURN:
				self.gen_re()
			elif self.p.commandType() == CT.C_CALL:
				self.gen_call(self.p.arg2(), self.p.arg3())
			elif self.p.commandType() == CT.C_FUNCTION:
				self.gen_func(self.p.arg2(), self.p.arg3())

		if self.verbose:
			pprint(self.asms)

	def write(self, path):
		with open(path, "w") as f:
			f.writelines([f"{line}\n" for line in self.asms])

if __name__ == "__main__":
	verbose = True
	path = sys.argv[1]
	if os.path.isdir(path):
		print(f"Translate dir {path}")
		outname = path.split("/")[-1] + ".asm"
		outpath = os.path.join(path, outname)
		asms = []
		file_list = list(glob(f"{path}/*vm"))
		for i, f in enumerate(file_list):
			print(f"Sub file: {f}")
			t = Translator(f, verbose=verbose)
			if i == 0:
				t.gen_init()
			t.gen()
			asms.extend(t.asms)
		with open(outpath, "w") as f:
			f.writelines([f"{line}\n" for line in asms])
	else:
		print(f"Translate file {path}")
		outpath = path.replace(".vm", ".asm")
		t = Translator(path, verbose=verbose)
		t.gen()
		t.write(outpath)
	print(f"Wrote to {outpath}")


