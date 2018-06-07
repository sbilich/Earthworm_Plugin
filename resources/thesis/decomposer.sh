# Add to Python path.
export PYTHONPATH=$PYTHONPATH://home/ngarg/thesis://home/ngarg/thesis/src

# Create copy of output file.
DIR=~ngarg/thesis/files/$USER
if [ ! -d $DIR ]
then
    mkdir $DIR
fi
cat $1 > $DIR/output

# Run decomposer.
cd ~ngarg/thesis &&
python3 -m src.decomposer $DIR/output $2
