source ~/.zshrc
conda activate dev
#cd projects/07
#python3 translator.py MemoryAccess/PointerTest/PointerTest.vm
#python3 translator.py MemoryAccess/StaticTest/StaticTest.vm
#python3 translator.py MemoryAccess/BasicTest/BasicTest.vm

#cd projects/08
#python3 translator.py ProgramFlow/BasicLoop/BasicLoop.vm
#python3 translator.py ProgramFlow/FibonacciSeries/FibonacciSeries.vm
#python3 translator.py FunctionCalls/SimpleFunction/SimpleFunction.vm
#python3 translator.py FunctionCalls/NestedCall/Sys.vm
#python3 translator.py FunctionCalls/FibonacciElement
#python3 translator.py FunctionCalls/StaticsTest


#./tools/JackCompiler.sh projects/09/Square
#python3 projects/08/translator.py projects/09/Square


#./tools/JackCompiler.sh projects/09/Life
#python3 projects/08/translator.py projects/09/Life

cd projects/10

python3 compiler.py Square
../../tools/TextComparer.sh Square/SquareT.xml Square/SquareTOut.xml
../../tools/TextComparer.sh Square/SquareGameT.xml Square/SquareTGameOut.xml
../../tools/TextComparer.sh Square/MainT.xml Square/MainTOut.xml
../../tools/TextComparer.sh Square/Square.xml Square/SquareOut.xml
../../tools/TextComparer.sh Square/SquareGame.xml Square/SquareGameOut.xml
../../tools/TextComparer.sh Square/Main.xml Square/MainOut.xml


python3 compiler.py ArrayTest 
../../tools/TextComparer.sh ArrayTest/MainT.xml ArrayTest/MainTOut.xml
../../tools/TextComparer.sh ArrayTest/Main.xml ArrayTest/MainOut.xml

python3 compiler.py ExpressionLessSquare
../../tools/TextComparer.sh ExpressionLessSquare/SquareT.xml ExpressionLessSquare/SquareTOut.xml
../../tools/TextComparer.sh ExpressionLessSquare/SquareGameT.xml ExpressionLessSquare/SquareGameTOut.xml
../../tools/TextComparer.sh ExpressionLessSquare/MainT.xml ExpressionLessSquare/MainTOut.xml

../../tools/TextComparer.sh ExpressionLessSquare/Square.xml ExpressionLessSquare/SquareOut.xml
../../tools/TextComparer.sh ExpressionLessSquare/SquareGame.xml ExpressionLessSquare/SquareGameOut.xml
../../tools/TextComparer.sh ExpressionLessSquare/Main.xml ExpressionLessSquare/MainOut.xml
