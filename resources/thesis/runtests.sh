python -m unittest discover
python3 -m unittest discover

# coverage run -m unittest discover -s tests
coverage run --source=src -m unittest discover -s tests
coverage report -m
