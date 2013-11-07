TARBALL=ucsql.v0.1.tar

dist:
	@echo "Creating Distribution File ..."
	tar cvf ${TARBALL} ./EXAMPLES.txt  ./get_schema_files*  ./LICENSE.txt  ./Makefile  ./README.txt  ./scripts/  ./setup.py  ./src
	
all:
	./get_schema_files
	python setup.py install
