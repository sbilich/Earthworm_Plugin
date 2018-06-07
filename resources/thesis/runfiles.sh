# python -m src.decomposer codesample/python2/simple_str.py
# python3 -m src.decomposer codesample/python3/simple_str.py

# python -m src.decomposer codesample/python2/simple_loop.py
# python3 -m src.decomposer codesample/python3/simple_loop.py

# python -m src.decomposer codesample/python2/nested_for_loop.py

# python -m src.decomposer codesample/python2/conditional_with_elif.py
# python3 -m src.decomposer codesample/python3/conditional_with_elif.py

# python -m src.decomposer codesample/python2/simple_reaching_def.py
# python3 -m src.decomposer codesample/python3/simple_reaching_def.py

# python -m src.decomposer codesample/student_solution/hw5/13/cast.py
# python -m src.decomposer codesample/student_solution/hw4/31/cast.py

# # python -m src.decomposer codesample/student_solution/hw5/19/cast.py
# # python -m src.decomposer codesample/professor_solution/hw5/cast.py

# # python -m src.decomposer codesample/student_solution/hw5/26/cast.py
# # python -m src.decomposer codesample/student_solution/hw5/27/cast.py

# # All authors put functions inside functions.
# python -m src.decomposer codesample/python2/hw4_cast_1.py
# python -m src.decomposer codesample/student_solution/hw5/1/cast.py
# python -m src.decomposer codesample/student_solution/hw5/30/cast.py
# python -m src.decomposer codesample/student_solution/hw5/58/cast.py


# Generally problematic files.
# python -m src.decomposer codesample/student_solution/hw5/3/cast.py
# python -m src.decomposer codesample/student_solution/hw5/10/cast.py
# python -m src.decomposer codesample/student_solution/hw5/11/cast.py
# python -m src.decomposer codesample/student_solution/hw5/18/cast.py

# Not compiling files.
# python -m src.decomposer codesample/student_solution/hw5/48/cast.py

# # Not fully working for diff_ref_livar.
# python -m src.decomposer codesample/student_solution/hw5/33/cast.py
# python -m src.decomposer codesample/student_solution/hw5/34/cast.py
# python -m src.decomposer codesample/student_solution/hw5/37/cast.py
# python -m src.decomposer codesample/student_solution/hw5/39/cast.py
# python -m src.decomposer codesample/student_solution/hw5/52/cast.py

# FILES TO 100% EXAMINE FOR FRIDAY.
# Talking 4/7/2017
# python -m src.decomposer codesample/student_solution/hw4/4/cast.py
# time python -m src.decomposer codesample/student_solution/hw4/14/cast.py --slow # TODO: Look @.
# python -m src.decomposer codesample/student_solution/hw6/14/blur.py

# Generates many good looking suggestions. Difference between fast & slow.
# # # # time python -m src.decomposer codesample/student_solution/hw5/41/cast.py --slow
# # # # time python -m src.decomposer codesample/student_solution/hw5/36/cast.py --slow
# # # time python -m src.decomposer codesample/student_solution/hw5/33/cast.py --slow # Generates a lot of good suggesitons
# # time python -m src.decomposer codesample/student_solution/hw5/18/cast.py --slow
# time python -m src.decomposer codesample/student_solution/hw5/19/cast.py --slow # Not getting too many suggestions - b/ fewer lines of code.
# # # # time python -m src.decomposer codesample/student_solution/hw4/14/cast.py --slow
# # # # time python -m src.decomposer codesample/student_solution/hw5/27/cast.py --slow # Really interesting result.
# time python -m src.decomposer codesample/student_solution/hw5/50/cast.py
# time python -m src.decomposer codesample/student_solution/hw5/50/cast.py --slow # Keep an eye on suggestion 59-71, 82-96.
# # # time python -m src.decomposer codesample/student_solution/hw5/47/cast.py --slow # Good results.
# time python -m src.decomposer codesample/student_solution/hw5/33/cast.py --slow

# Use for linter.
# time python -m src.decomposer codesample/student_solution/hw5/57/cast.py --slow

# Future work examples.
# time python -m src.decomposer codesample/student_solution/hw5/19/cast.py --slow # I don't find suggestions for extra long lines.
# time python -m src.decomposer codesample/student_solution/hw5/63/cast.py --slow # Examine inividual lines of code.
