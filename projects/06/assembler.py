import sys
import enum


class CommandType(enum.Enum):
	A_COMMAND = 1
	C_COMMAND = 2
	L_COMMAND = 3
	UNKNOWN   = 4

class Parser():
	def __init__(self, path):
		with open(path) as f: self.lines = f.read().strip().split("\n")
		self.icommand = 0

	def advance(self):
		
		assert self.icommand < len(self.lines), "Out of command"
		self.command = self.lines[self.icommand].strip()
		self.icommand += 1
		if self.command.strip().startswith('//') or len(self.command) == 0:
			self.advance()
			return
		if "//" in self.command:
			self.command = self.command[:self.command.index('//')].strip()

		if self.command.startswith("@") and len(self.command) > 1:
			self._command_type = CommandType.A_COMMAND
		elif self.command.startswith("(") and self.command.endswith(")") and len(self.command) > 2:
			self._command_type = CommandType.L_COMMAND
		else: self._command_type = CommandType.C_COMMAND

		self._dest = self.command.split("=")[0] if "=" in self.command else ""
		self._comp = self.command.split(";")[0] if ";" in self.command else self.command
		self._comp = self.command.split("=")[1] if "=" in self.command else self._comp
		self._jump = self.command.split(";")[1] if ";" in self.command else ""


	def hasMoreCommands(self):
		return self.icommand < len(self.lines)

	def commandType(self):
		return self._command_type

	def symbol(self):
		assert self.commandType() == CommandType.A_COMMAND \
				or self.commandType() == CommandType.L_COMMAND, "Expect command type A or L"
		if self.commandType() == CommandType.A_COMMAND:
			return self.command[1:]
		else:
			return self.command[1:-1]

	def dest(self):
		assert self._command_type == CommandType.C_COMMAND, "Expect command type C"
		return self._dest

	def comp(self):
		assert self._command_type == CommandType.C_COMMAND, "Expect command type C"
		return self._comp

	def jump(self):
		assert self._command_type == CommandType.C_COMMAND, "Expect command type C"
		return self._jump

	def reset(self):
		self.icommand = 0

class Code():
	
	def gen_a(self, addr):
		return '0' + self._bits(addr).zfill(15)

	def gen_c(self, dest, comp, jump):
		return '111' + self.comp(comp) + self.dest(dest) + self.jump(jump)

	def dest(self, s):
		return f"{1 if 'A' in s else 0}{1 if 'D' in s else 0}{1 if 'M' in s else 0}"

	_comp_codes = {'0': '0101010', '1': '0111111', '-1': '0111010', 'D': '0001100', 
			'A': '0110000', '!D': '0001101', '!A': '0110001', '-D': '0001111', '-A': '0110011', 
			'D+1': '0011111', 'A+1': '0110111', 'D-1': '0001110', 'A-1': '0110010', 'D+A': '0000010', 
			'D-A': '0010011', 'A-D': '0000111', 'D&A': '0000000', 'D|A': '0010101', '': 'xxxxxxx', 
			'M': '1110000', '!M': '1110001', '-M': '1110011', 'M+1': '1110111', 'M-1': '1110010', 
			'D+M': '1000010', 'D-M': '1010011', 'M-D': '1000111', 'D&M': '1000000', 'D|M': '1010101'}
	def comp(self, c):
		return self._comp_codes[c]

	_jump_codes = ['', 'JGT', 'JEQ', 'JGE', 'JLT', 'JNE', 'JLE', 'JMP']
	def jump(self, j):
		return self._bits(self._jump_codes.index(j)).zfill(3)

	def _bits(self, n):
		return bin(int(n))[2:]



class Assembler():
	def __init__(self, path):
		self.p = Parser(path)
		self.c = Code()
		self._current_rom = 0
		self._current_symbol = 16
		self.SymbolTable = {}


	def buildSymbolTable(self):
		self._current_rom = 0
		self.SymbolTable = {
				"SP": 0, "LCL": 1, "ARG":2, "THIS": 3, "THAT": 4, 
				"R0": 0,"R1": 1,"R2": 2,"R3": 3,"R4": 4,"R5": 5,"R6": 6,"R7": 7,"R8": 8,
				"R9": 9,"R10": 10,"R11": 11,"R12": 12,"R13": 13,"R14": 14,"R15": 15,
				"SCREEN": 16384, "KBD": 24576
				}

		self.p.reset()
		while self.p.hasMoreCommands():
			self.p.advance()
			if self.p.commandType() == CommandType.C_COMMAND or self.p.commandType() == CommandType.A_COMMAND:
				self._current_rom += 1
			elif self.p.commandType() == CommandType.L_COMMAND:
				self.SymbolTable[self.p.symbol()] = self._current_rom

	def generate(self):
		self.p.reset()
		binaries = []
		while self.p.hasMoreCommands():
			self.p.advance()
			if self.p.commandType() == CommandType.A_COMMAND:
				if self.p.symbol() not in self.SymbolTable.keys():
					if self.p.symbol().isnumeric():
						addr = self.p.symbol()
					else:
						addr = self._current_symbol
						self._current_symbol += 1
					self.SymbolTable[self.p.symbol()] = addr
				else:
					addr = self.SymbolTable[self.p.symbol()]

				binaries.append(self.c.gen_a(addr))
			elif self.p.commandType() == CommandType.C_COMMAND:
				binaries.append(self.c.gen_c(self.p.dest(), self.p.comp(), self.p.jump()))
		return binaries

	def write(self, path, lines):
		with open(path, "w") as f:
			f.writelines([f"{line}\n" for line in lines])



if __name__ == "__main__":
	print(sys.version)
	filename = sys.argv[1]
	print(f"Parsing file {filename}")
	a = Assembler(filename)
	a.buildSymbolTable()
	binary = a.generate()
	a.write(filename.replace(".asm", ".hack"), binary)
	print(f"Wrote to {path}")


