all: dist upload

dist: 
	python3 setup.py sdist bdist_wheel

upload:
	twine check dist/*
	twine upload dist/*

clean:
	rm -rf build dist *.egg-info .eggs
