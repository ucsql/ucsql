#!/usr/bin/env python
#
# setup_setup.py for 'ucsql'
#
# This is the 'easy button' for installation of 'ucsql'
# Given the many dependencies, this script will optionally go an install everything it needs.
# If admins wish to install packages manually, then they can skip this.
# This script is assumed to be run from 'setup.py', but can be run standalone.
# Any missing pre-requisites will be flagged during the normal 'setup.py'
#

import sys
import os
import glob

#
# Make sure we have what we might need
#
# Many packages don't install properly with 'pip', so install them here via 'yum' or 'zypper'
#
# 'linuxprereqs' includes the dependency, and the determinator.  Assumes local package installe (yum, zypper, ...)
#
# 'lxml' has too many dependencies to install manually as a pythonprereq.  Install via yum/zypper
#
linuxprereqs = { "wget" : "which wget >/dev/null 2>&1", 
		 "gcc"  : "which gcc >/dev/null 2>&1",
		 "python-devel" : "rpm -qa | grep python-dev 2>&1",
		 "python-lxml"  : "rpm -qa | grep lxml 2>&1"
               }

#
# 'pythonpreqs' include the module needed and the source URL if it needs to be installed
#
# 'setuptools', 'pip', etc are not 100% consistent/reliable, so we'll do it by hand
#

pythonprereqs = { 
#	'lxml' : { 'namevers' : 'lxml-3.2.3', 'wget' : 'https://pypi.python.org/packages/source/l/lxml/lxml-3.2.3.tar.gz#md5=fef47bb4ac72ac38ce778518dac42236' } ,
	'setuptools' : { 'namevers' : 'setuptools-1.4.1', 'wget': 'https://pypi.python.org/packages/source/s/setuptools/setuptools-1.4.1.tar.gz#md5=65bb270fbae373c26a2fa890ad907818'} ,
	'Crypto' : { 'namevers' : 'pycrypto-2.6.1', 'wget': 'https://ftp.dlitz.net/pub/dlitz/crypto/pycrypto/pycrypto-2.6.1.tar.gz'},
	'pyparsing' : { 'namevers' : 'pyparsing-2.0.1', 'wget' : 'http://cheeseshop.python.org/packages/source/p/pyparsing/pyparsing-2.0.1.tar.gz' }
		}

def install_this(mod):
	cmd = "wget --no-check-certificate " + pythonprereqs[mod]['wget']
	print cmd
	os.system (cmd)
	cmd = "tar xzvf " + pythonprereqs[mod]['namevers'] + ".tar.gz"
	print cmd
	os.system (cmd)
	os.chdir (pythonprereqs[mod]['namevers'])
	os.system ("python setup.py install")
	os.chdir ("..")


def main():

	linux = os.popen("egrep 'Linux|CentOS' /etc/issue").readline()
	if ('Red Hat' in linux or 'CentOS' in linux):
		cmd = "yum install -y "
	elif ('SUSE' in linux):
		cmd = "zypper install -y "
	else:
		print "Sorry, but your Linux distro %s is not yet supported" % linux
		return -1
	
	for i in linuxprereqs:
		dep = os.system (linuxprereqs[i])
		if dep != 0:
			tcmd = cmd + i
			print
			print "About to run '%s'" % tcmd 
			try:
				raw_input( "Okay? [ or hit ^C ]")
			except:
				print
				print "Exiting ..."
				return -1
			print tcmd
			os.system (tcmd)
		else:
			print i, " is currently installed"
	
	for i in pythonprereqs:
		pcmd = "python -c \"import %s\" > /dev/null 2>&1" % i  
		if os.system (pcmd) != 0:
			print
			print i + " : Not found.  Installing from : " + pythonprereqs[i]['wget']
			print
			install_this (i)

	try:
		import pkg_resources
	except ImportError:
		print "Missing 'pkg_resources'.   Please run 'curl https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | python'"
		print "... and then rerun this install script"
		return -1
	try:
		from setuptools import setup
	except ImportError:
		from distutils.core import setup
	
	
	#
	# Make sure 'generateDS' is installed.  Need to download/install directly, if needed.
	#
	generateDS = os.popen ("which generateDS.py 2>/dev/null").read().strip()
	if generateDS == "":
		# Go install it.
		os.system ("wget --no-check-certificate https://pypi.python.org/packages/source/g/generateDS/generateDS-2.12a.tar.gz#md5=69e60733668c95ae26f9f6da0576cbfc; tar xzvf generateDS-2.12a.tar.gz; cd generateDS-2.12a; python setup.py install; cd ..")
	
	
	#
	# Remove XML boogers, if any.  These represent conflicts with generateDS/lxml
	#
	boogers = ['/usr/lib64/python2.*/site-packages/_xmlplus',
		   '/usr/local/lib/python2.*/site-packages/_xmlplus',
		   '/usr/local/lib/python2.*/dist-packages/_xmlplus',
		   '/usr/lib/python2.*/site-packages/_xmlplus' ]
	
	for b in boogers:
		if glob.glob(b):
			print "The '_xmlplus' directory has been detected in : ", glob.glob(b)
			print "This will unfortunately conflict with the 'lxml' package libraries"
			print "If you can, please delete the %s directory, and then rerun this setup script" % glob.glob(b)
			return -1

	return 0
	
if __name__ == "__main__":
        sys.exit(main())

