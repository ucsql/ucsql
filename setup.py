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
import glob

#
# Make sure we have what we might need
#
# many packages don't install properly with 'pip', so install them here via 'yum'
#
prereqs = ["wget ", "gcc ", "python-crypto ", "python-lxml ", "python-setuptools " ]
print 
print "'ucsql' requires the following packages: ", prereqs
print 
print "'yum' will not update any packages that are already installed."
print

print
cmd = "yum install -y "
for i in prereqs:
	cmd += i

print "About to run '%s'" % cmd 
try:
	raw_input( "Okay? [ or hit ^C ]")
except:
	print
	print "Exiting ..."
	sys.exit(-1)
os.system(cmd)

try:
	import pkg_resources
except ImportError:
	print "Missing 'pkg_resources'.   Please run 'curl https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | python'"
	print "... and then rerun this install script"
	sys.exit(-1)
try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup


name='ucsql'

cwd = os.getcwd()
srcdir = cwd + "/src/ucsql"
central_schema = "Schema-UCS_Central_1.1.1b"
central_tarball = "https://communities.cisco.com/servlet/JiveServlet/download/37092-3-55383/" + central_schema + ".tar.gz"

ucsm_schema = "Schema-2.1.3a"
ucsm_tarball = "https://communities.cisco.com/servlet/JiveServlet/download/36350-4-55358/" + ucsm_schema + ".tar.gz"

tmpdir = "/tmp/ucsql.%s" % os.getpid()

boogers = ['/usr/lib64/python2.*/site-packages/_xmlplus',
	   '/usr/local/lib/python2.*/site-packages/_xmlplus',
	   '/usr/local/lib/python2.*/dist-packages/_xmlplus',
	   '/usr/lib/python2.*/site-packages/_xmlplus' ]

for b in boogers:
	if glob.glob(b):
		print "The '_xmlplus' directory has been detected in : ", glob.glob(b)
		print "This will unfortunately conflict with the 'lxml' package libraries"
		print "If you can, please delete the %s directory, and then rerun this setup script" % glob.glob(b)
		sys.exit(-1)

#
# Make sure 'generateDS' is installed
#
generateDS = os.popen ("which generateDS.py 2>/dev/null").read().strip()
if generateDS == "":
	# Go install it.
	os.system ("wget --no-check-certificate https://pypi.python.org/packages/source/g/generateDS/generateDS-2.12a.tar.gz#md5=69e60733668c95ae26f9f6da0576cbfc; tar xzvf generateDS-2.12a.tar.gz; cd generateDS-2.12a; python setup.py install; cd ..")
	generateDS = os.popen ("which generateDS.py 2>/dev/null").read().strip()

schema_name_map = {
	"stats" : { "in" : central_schema + "/stats-mgr.out.xsd", "out" : srcdir + "/stats.py"},
	"idm" : { "in" : central_schema + "/identifier-mgr.out.xsd", "out": srcdir + "/idm.py"},
	"ops" : { "in" : central_schema + "/operation-mgr.out.xsd", "out": srcdir + "/ops.py"},
	"policy" : { "in" : central_schema + "/policy-mgr.out.xsd", "out" : srcdir + "/policy.py"},
	"service" : { "in" : central_schema + "/service-reg.out.xsd", "out" : srcdir + "/service.py"},
	"resource" : { "in" : central_schema + "/resource-mgr.out.xsd", "out" : srcdir + "/resource.py"},
	"ucsm" : { "in" : ucsm_schema + "/UCSM-OUT.xsd", "out" : srcdir + "/ucsm.py" }
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
for s in schema_name_map:
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
	version=0.14,
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
                "pyparsing >= 1.5.7",
	]
	)
