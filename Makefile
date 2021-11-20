all: dist upload

build:
	python setup.py build_ext --inplace

dist: 
	python3 setup.py sdist bdist_wheel

upload:
	twine check dist/*
	twine upload dist/*

clean:
	rm -rf build dist *.egg-info .eggs
	rm -f htmlgenerator.c
	rm -f *.so

raise_and_release_minor_version:
	git push
	NEWVERSION=$$(                              \
	   echo -n '__version__ = ' &&              \
	   cat htmlgenerator/__init__.py | grep __version__ |            \
	   cut -d = -f 2 |                          \
	   python3 -c 'i = input().strip().strip("\""); print("\"" + ".".join(i.split(".")[:-1] + [str(int(i.split(".")[-1]) + 1) + "\""]))' \
) &&                                        \
	sed -i "s/.*__version__.*/$$NEWVERSION/g" htmlgenerator/__init__.py
	git commit -m 'bump version' htmlgenerator/__init__.py && git push && git push --tags
