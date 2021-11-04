all: dist upload

dist: 
	python3 setup.py sdist bdist_wheel

upload:
	twine check dist/*
	twine upload dist/*

clean:
	rm -rf build dist *.egg-info .eggs

raise_and_release_minor_version:
	git push
	NEWVERSION=$$(                              \
	   echo -n '__version__ = ' &&              \
	   cat bread/__init__.py |            \
	   cut -d = -f 2 |                          \
	   python3 -c 'i = input().strip().strip("\""); print("\"" + ".".join(i.split(".")[:-1] + [str(int(i.split(".")[-1]) + 1) + "\""]))' \
) &&                                        \
	echo $$NEWVERSION > bread/__init__.py
	git commit -m 'bump version' bread/__init__.py && git push && git push --tags

