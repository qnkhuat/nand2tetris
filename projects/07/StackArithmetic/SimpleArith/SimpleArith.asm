// push constant 8
@8
D=A
@SP
A=M
M=D
@SP
M=M+1
// pop argument 2
@SP
A=M-1
D=M
@R5
M=D
@ARG
D=M
@2
D=D+A
@R6
M=D
@R5
D=M
@R6
A=M
M=D
@SP
M=M-1
