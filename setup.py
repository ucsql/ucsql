#!/usr/bin/env python
#
# setup.py for 'ucsql'
#
# 'ucsql' is dependent on the UCSM and UCS Central Schema files, published by Cisco
# on the Communities Site:   http://communities.cisco.com/ucs
#
# This setup process does the following:
#
#	- Download all the Schema Files from 'well known' sites, using 'wget'.  Uncompress, etc.
#	- Run 'generateDS.py' on the Schema Files to create the corresponding Python classes for the various DME's
#	- Then go through standard Python 'setup()' to build and install
#

import sys
import os
import pkg_resources
from setuptools import setup

name='ucsql'

cwd = os.getcwd()
srcdir = cwd + "/src/ucsql"
central_schema = "Schema-UCS_Central_1.1.1b"
central_tarball = "https://communities.cisco.com/servlet/JiveServlet/download/37092-3-55383/" + central_schema + ".tar.gz"

ucsm_schema = "Schema-2.1.3a"
ucsm_tarball = "https://communities.cisco.com/servlet/JiveServlet/download/36350-4-55358/" + ucsm_schema + ".tar.gz"

tmpdir = "/tmp/ucsql.%s" % os.getpid()

#
# Make sure 'lxml' version is 3.2.3 before trying to run 'generateDS' 
#
if pkg_resources.get_distribution('lxml').version != '3.2.3':
	print
	print "'ucsql' requires 'lxml' version 3.2.3.   Please download from http://lxml.de/files/lxml-3.2.3.tgz"
	print
	sys.exit(-1)

generateDS = os.popen ("which generateDS.py 2>/dev/null").read().strip()
if generateDS == "":
	print
	print "'ucsql' requires the 'generateDS.py' package.   Please download from https://pypi.python.org/pypi/generateDS/"
	print
	sys.exit(-1)

schema_name_map = {
	"stats" : { "in" : central_schema + "/stats-mgr.in.xsd", "out" : srcdir + "/stats.py"},
	"idm" : { "in" : central_schema + "/identifier-mgr.in.xsd", "out": srcdir + "/idm.py"},
	"ops" : { "in" : central_schema + "/operation-mgr.in.xsd", "out": srcdir + "/ops.py"},
	"policy" : { "in" : central_schema + "/policy-mgr.in.xsd", "out" : srcdir + "/policy.py"},
	"service" : { "in" : central_schema + "/service-reg.in.xsd", "out" : srcdir + "/service.py"},
	"resource" : { "in" : central_schema + "/resource-mgr.in.xsd", "out" : srcdir + "/resource.py"},
	"ucsm" : { "in" : ucsm_schema + "/UCSM-IN.xsd", "out" : srcdir + "/ucsm.py" }
}

os.system ("mkdir %s" % tmpdir)
os.chdir(tmpdir)
os.system ("wget %s" % central_tarball)
os.system ("wget %s" % ucsm_tarball)
os.system ("tar xzvf %s" % central_schema + ".tar.gz")
os.system ("tar xzvf %s" % ucsm_schema + ".tar.gz")

print """

Generating UCS DME Python classes from Schema files.
Note:  This could take anywhere from 10 - 60 minutes depending on CPU and Memory,
so please be patient (or find a bigger system).

"""

os.system ("mkdir -p %s" % srcdir)
for s in schema_name_map.keys():
	cmd = "python %s -o %s --member-specs=dict %s" % \
			(generateDS, schema_name_map[s]["out"], schema_name_map[s]["in"])
	print cmd
	os.system (cmd)

os.system ("rm -rf %s" % tmpdir)
os.chdir (cwd)

def is_package(path):
	return (
			os.path.isdir(path) and
			os.path.isfile(os.path.join(path, '__init__.py'))
			)

def find_packages(path, base="" ):
	packages = {}
	for item in os.listdir(path):
		dir = os.path.join(path, item)
		if is_package( dir ):
			if base:
				module_name = "%(base)s.%(item)s" % vars()
			else:
				module_name = item
			packages[module_name] = dir
			packages.update(find_packages(dir, module_name))
	return packages

setup(
	name=name,
	version='0.1',
	description='SQL-like interface for UCS Manager and UCS Central',
	author='Cisco Systems',
	author_email='',
	long_description='Install Instructions: sudo python setup.py install',
	packages=find_packages('src'),
	package_dir = {'': 'src'},
	scripts = ['scripts/ucsql'],
	namespace_packages=['ucsql'],
	include_package_data = True,
	zip_safe = False,
	install_requires=[
		"lxml >= 3.2.3",
		"pyparsing >= 1.5.7",
		"pycrypto >= 2.6.1",
	]
	)
