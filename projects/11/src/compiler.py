import xml.etree.ElementTree as ET
import sys, os, glob
from enum import Enum

from tokenizer import TokenType, Tokenizer
from engine import CompilationEngine
from utils import *


class Compiler:
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
			c = Compiler(os.path.join(path, f))
			c.gen()
	else:
		print(f"Compiling file {path}")
		c = Compiler(path)
		c.gen()


