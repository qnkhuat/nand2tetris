// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/07/StackArithmetic/SimpleArith/SimpleAddVME.tst

load SimpleArith.vm,
output-file SimpleArith.out,
compare-to SimpleArith.cmp,
output-list RAM[0]%D2.6.2 RAM[256]%D2.6.2;

set RAM[0] 256,  // initializes the stack pointer
set RAM[1] 300,   // base address of the local segment
set RAM[2] 400,   // base address of the argument segment
set RAM[3] 3000,  // base address of the this segment
set RAM[4] 3010,  // base address of the that segment

repeat 3 {       // SimpleArith.vm has 3 instructions
  vmstep;
}

output;          // the stack pointer and the stack base
