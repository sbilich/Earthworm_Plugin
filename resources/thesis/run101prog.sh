HW_NUM=hw5

# Runs student code.
FILES=codesample/student_solution/$HW_NUM/*/cast.py
for f in $FILES
do
    # echo "Running file... $f"
    python -m src.decomposer $f --noprogress --slow
done

# Runs professor code.
FILE=codesample/professor_solution/$HW_NUM
if [ $HW_NUM == 'hw4' ]
then
    PROF_FILENAME=$FILE/part5/cast.py
else
    PROF_FILENAME=$FILE/cast.py
fi
# echo "\nProfessor solution... $PROF_FILENAME"
python -m src.decomposer $PROF_FILENAME --noprogress --slow
