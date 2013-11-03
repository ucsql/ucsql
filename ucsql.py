#!/usr/local/bin/python
#
# ucsql : A simple SQL interface in to UCS DME (one or many).  
#		  Intended to work against both/either UCSM or UCS Central.
#
# Dependencies:
#		This was initially built on python 2.5.6
#
#		Assumes that the imported DME modules (from UCS or UCS Central) are Python files that have been
#		code-generated from 'generateDS.py --member-specs=dict'.   Ex:
#			   python `which generateDS.py` -o stats.py --member-specs=dict stats-mgr.out.xsd
#		.xsd files are assumed to be code-generated schema files from the corresponding DME
#
#		... and generateDS.py depends on the lxml package ...
#
#		The SQL front end depends on the 'pyparsing' package and has been 
#		shamelessly pillaged from: 
#			http://pyparsing.wikispaces.com/file/view/simpleSQL.py/30112834/simpleSQL.py
# 		Copyright (c) 2003, Paul McGuire
#
#	History:
#		- 	Until we have a "virtual MIT" for Central, this is the only programmatic tool in town.
#
#	In Case of Emergency:
#		-   Call 911
#		-	http://communities.cisco.com/ucs
#	
#	Original Author:
#		- Jeff Silberman (jesilber@cisco.com)  (@jsilberm)
#
#	Contributing Authors:
#		- <your name goes here>
#
#	Legal Disclaimer:
#		- "You're on your own. Use at your own risk."
#
#	Seriously:
#		- Cisco Systems Assumes absolutely no liability, nor do I.
#
#	TODO:
#		- overwrite/recreate session files
#		- Improve Security and Sessions 
#		- BSD/GPL License
#		- setup.py, Packaging
#		- output in csv/html format
#		- Support "insert" commands
#		- Support "delete" commands
#		- Support "update" commands
#		- Support inhierarchical
#		- 2 table joins
#		- github project
#		- developer/community email alias (communities.cisco.com?)
#		- bugzilla 
#		- Common virtual interface for UCS Central DMEs and external stats database
#		- run as a DB server target
#


from os import *
from os.path import *
import sys
import re
import urllib2
from optparse import OptionParser
import xml.dom.minidom
from getpass import getpass
from ops import *
from ucsm import *
from policy import *
from idm import *
from resource import *
from stats import *
from service import *
from optparse import OptionParser
from Crypto.Cipher import ARC4
import random
import base64
import inspect
from pyparsing import Literal, CaselessLiteral, Word, Upcase, delimitedList, Optional, \
	Combine, Group, alphas, nums, alphanums, ParseException, Forward, oneOf, quotedString, \
	ZeroOrMore, restOfLine, Keyword

class ucsdme:
	def __init__ (self, url, login, passwd):
		self.url = url
		self.login = login
		self.passwd = passwd
		self.cookie = None
		self.headers = {'Content-type': 'text/xml'}
		body = """
				<aaaLogin inName="%s" inPassword="%s"/>
			   """  % (self.login, self.passwd)
		content = self._ucs_req (body)
		# print "ucsdme.init:  ", content
		for word in content.split():
			match = re.search(r'outCookie=(.*)', word)
			if match:
				self.cookie= match.group(1)
		if (self.cookie == None):
			raise Exception("Login Error")

	def __del__(self):
		try:
			body = '<aaaLogout inCookie=%s/>' % self.cookie
			content = self._ucs_req (body)
		except:
			pass
			# class_name = self.__class__.__name__
			# print class_name, "destroyed"
	
	def logout(self):
		try:
			body = '<aaaLogout inCookie=%s/>' % self.cookie
			content = self._ucs_req (body)
		except:
			pass

	def _ucs_req (self, data):
		# print "url = %s, data = %s, headers = %s" %(self.url, data, self.headers)
		req = urllib2.Request(url=self.url, data=data, headers=self.headers)
		return urllib2.urlopen(req).read()
	
	def resolve_class (self, klass, cols):
		body = """
			<configResolveClass cookie=%s 
				inHierarchical="false" classId="%s"/>
			"""  % (self.cookie, klass)
		content = self._ucs_req (body)
		try:
			doc = xml.dom.minidom.parseString(content)
		except:
			return None
		# print doc.toprettyxml()
		if (cols == "*"):
			cols = []
			node = doc.getElementsByTagName(klass)[0]
			for n in node.attributes.items():
				cols.append(n[0])
		hdr = ""
		dash = ""
		for i in cols:
			hdr += "	" + i
			dash += "	" + '-' * len(i)
		header = hdr + "\n" + dash
		oput = ""
		for node in doc.getElementsByTagName(klass):
			if (cols == "*"):
				cols = []
				for n in node.attributes.items():
					cols.append(n[0])
			oput += "\n"
			for col in cols:
					val = node.getAttribute(col)
					oput += "	" + val
		return header + oput
					
	def config_confmos (self, klass, dn, status):
		body = """
			<configConfMos cookie=%s 
				inHierarchical="false"> 
				<inConfigs> <pair key=%s> <%s dn=%s status="%s" /> </pair> </inConfigs>
			</configConfMos> 
			""" % (self.cookie, dn, klass, dn, status)
		content = self._ucs_req (body)
		# print content
		try:
			doc = xml.dom.minidom.parseString(content)
			node = doc.getElementsByTagName(klass)[0]
			odn = '"' + node.getAttribute("dn") + '"'
			# Sanity check on xml return output
			if (odn == dn):					
				return 1
			else:
				return None
		except:
			return None

################################################
#
#	ucsqlGrammar
#
# Shamelessly pillaged from: http://pyparsing.wikispaces.com/file/view/simpleSQL.py/30112834/simpleSQL.py
#
# Copyright (c) 2003, Paul McGuire
#
################################################

	
class ucsqlGrammar:
	def __init__ (self, str):

		self.str = str

		# define tokens
		selectStmt = Forward()
		showStmt	= Forward()
		helpStmt 	= Forward()
		selectToken = Keyword("select", caseless=True)
		fromToken   = Keyword("from", caseless=True)
		showToken	= Keyword("show", caseless=True)
		helpToken   = Keyword("help", caseless=True) | Keyword("?", caseless=True)
		
		ident          = Word( alphas, alphanums + "_$" ).setName("identifier")
		# columnName     = Upcase ( delimitedList( ident, ".", combine=True ) )
		columnName     = Word( alphas )
		columnNameList = Group( delimitedList( columnName ) )
		#  tableName      = Upcase ( delimitedList( ident, ".", combine=True ) )
		tableName      = Word ( alphas )
		tableNameList  = Group( delimitedList( tableName ) )
		
		whereExpression = Forward()
		and_ = Keyword("and", caseless=True)
		or_ = Keyword("or", caseless=True)
		in_ = Keyword("in", caseless=True)
		
		E = CaselessLiteral("E")
		binop = oneOf("= != < > >= <= eq ne lt le gt ge", caseless=True)
		arithSign = Word("+-",exact=1)
		realNum = Combine( Optional(arithSign) + ( Word( nums ) + "." + Optional( Word(nums) )  |
											( "." + Word(nums) ) ) + 
		            	Optional( E + Optional(arithSign) + Word(nums) ) )
		intNum = Combine( Optional(arithSign) + Word( nums ) + 
		            	Optional( E + Optional("+") + Word(nums) ) )
		
		columnRval = realNum | intNum | quotedString | columnName # need to add support for alg expressions
		whereCondition = Group(
		    ( columnName + binop + columnRval ) |
		    ( columnName + in_ + "(" + delimitedList( columnRval ) + ")" ) |
		    ( columnName + in_ + "(" + selectStmt + ")" ) |
		    ( "(" + whereExpression + ")" )
		    )
		whereExpression << whereCondition + ZeroOrMore( ( and_ | or_ ) + whereExpression ) 
		
		# define the grammar
		selectStmt      << ( selectToken + 
		                   ( '*' | columnNameList ).setResultsName( "columns" ) + 
		                   fromToken + 
		                   tableNameList.setResultsName( "tables" ) + 
		                   Optional( Group( CaselessLiteral("where") + whereExpression ), "" ).setResultsName("where") )
		showStmt 		<< ( showToken  +
							 tableNameList.setResultsName( "tables" )) 
		helpStmt		<< ( helpToken )

		ucsqlGrammar = selectStmt | showStmt | helpStmt 

		self.tokens = ucsqlGrammar.parseString( str )

	def getTokens(self):
		return self.tokens

	def isSelect(self):
		return self.tokens[0] == "select"

	def isShow(self):
		return self.tokens[0] == "show"

	def isHelp(self):
		return (self.tokens[0] == "help" or self.tokens[0] == "?")

	def hasWhere(self):
		return self.tokens.where[0] != ""

	def getWhereClause(self):
		return self.tokens.where

	def getColumns(self):
		return self.tokens.columns

	def getTable(self):
		return self.tokens.tables[0]

	def test( self ):
		print self.str,"->"
		try:
			print "tokens = ",        self.tokens
			print "tokens.columns =", self.tokens.columns
			print "tokens.tables =",  self.tokens.tables
			print "tokens.where =", self.tokens.where
		except ParseException, err:
			print " "*err.loc + "^\n" + err.msg
			print err
		print

##################################################################

def TableExists(tblname):
	try:
		mtbl = globals()[tblname]
		return mtbl
	except:
		return None

def Format_Table(tblname, tbl):
	print "Table = ", tblname
	print "================================"
	mdi = tbl.member_data_items_
	for c in mdi:
		print "	", c


def ShowAll():
	print "All Objects ..."
	print "==================="
	for module in UCSVDME:
		try:
			m = sys.modules[module]
			for name, obj in inspect.getmembers(m):
				if (inspect.isclass(obj)):
					print "[%s] : %s" % (module, name)
		except:
			print "Error listing module", module

def Help():
	print "Command supported are:  'show table', 'select *|cols from table'"
	print
	print "Hit <Enter> to see full list of objects ..."
	sys.stdin.readline()	
	ShowAll()

def doSelectStmt(pstr):
	mo_name = pstr.getTable()
	if not TableExists(mo_name):
		print "Error: \"%s\" does not exist" % mo_name
		return 
	outp = None
	for h in MH:
		try:
			outp = MH[h].resolve_class ( mo_name, pstr.getColumns() )
			if outp:
				print outp
				return 
		except:
			# print "resolve_class call error"
			pass
	if not outp:
		print mo_name, ":  No such class"


def doShowStmt(pstr):
	tablename = pstr.getTable()
	mtbl = TableExists(tablename)
	if (mtbl):
		Format_Table ( tablename, mtbl )
	else:
		print "Error: \"%s\" does not exist" % tablename

def doStmt(stmt):
	try:
		pstr = ucsqlGrammar( stmt )
		#  pstr.test()
		if (pstr.isShow()):
			doShowStmt (pstr)
		elif (pstr.isSelect()):
			doSelectStmt (pstr)
		elif (pstr.isHelp()):
			Help()
	except:
		print "Error:  Problem parsing : ", stmt

#
# This needs help, but it's good enough for now, so that scripting can be done without password prompts.
# Eventually, this should tie in to "Authentication At Large", like LDAP, if possible
# Encoding the password doesn't really do anything, if the key and this code are both available.
# So if an intruder can already read 0400 files, then they're in.
#
def doSession(session, ipaddr=None):
	u = expanduser("~")
	kfile = u + "/._ucsqlk"
	
	if exists(kfile):
		f = file(kfile, "r")
		key = f.read()
		f.close()
	else:
		tsiv = "%s" % random.random()
		key = tsiv[2:10]
		f = file (kfile, "w")
		f.write(key)
		f.close()
		chmod(kfile, 0400)
	
	sfile = u + "/._ucsql:_" + session
	if exists(sfile):
		obj2 = ARC4.new(key)
		f = file(sfile, "r")
		inline = f.read().splitlines()
		ipaddr = inline[0].split()[2]
		user = inline[1].split()[2]
		b64epasswd = inline[2].split()[2]
		# print "ipaddr = ", ipaddr, ",  user = ", user, ", b64epasswd = ", b64epasswd
		b64d = base64.urlsafe_b64decode(b64epasswd)
		password = obj2.decrypt(b64d)
		# print "decrypted = ", password
	else:
		if ipaddr == None:
			ipaddr = raw_input('system name or IP addr: ')
		user = raw_input('login: ')
		password = getpass()
		obj1 = ARC4.new(key)
		cipher_text = obj1.encrypt(password)
		b64e = base64.urlsafe_b64encode(cipher_text)
		# print "key = ", key, " , text = ", b64e
		f = file(sfile, "w")
		f.write("ipaddr = %s\n" % ipaddr)
		f.write("user = %s\n" % user)
		f.write("password = %s\n" % b64e)
		f.close()
		chmod(sfile, 0400)
	return (ipaddr, user, password)

def Usage():
	print """
     Usage : ucsql [-u|--ucs= IPaddr] [-s|--session= \"session-name\"]
                   [-c|--command= \"command\"] [-v|--verbose]"

    -u|--ucs= IPaddr           : Name or IP address of UCSM or UCS Central instanace
    -s|--session= session-name : Name of session (to be used or created)
    -c|--command= command      : Run single command (non-interactive mode)
"""
	sys.exit(-1)


#################################################
#
#   Main
#
################################################

parser = OptionParser()
parser.add_option("-u", "--ucs", action="store", dest="ucsipaddr",
                  help="UCS IP Addr", metavar="COMMAND")
parser.add_option("-c", "--command", action="store", dest="command",
                  help="enter command on command line", metavar="COMMAND")
parser.add_option("-v", "--verbose",
                  action="store", action="store_true", dest="verbose", 
                  help="print status messages to stdout")
parser.add_option("-s", "--session", action="store", dest="session", 
					help="session name", metavar="COMMAND")

(options, args) = parser.parse_args(sys.argv)

if options.command:
	cmd = options.command
else:
	cmd = ""

if options.ucsipaddr and not options.session:
	ip = options.ucsipaddr
	user = raw_input ('login: ')
	password = getpass()
elif options.session:
	(ip, user, password) = doSession(options.session, options.ucsipaddr)
else:
	Usage()


connxstr = 'https://' + ip + ':443'
#
# Assumption :  The key name in UCSVDME is the same as the module name
#
UCSVDME = {
	'ucsm':  connxstr + '/nuova',
	'ops' :  connxstr + '/xmlIM/operation-mgr',
	'policy' : connxstr + '/xmlIM/policy-mgr',
 	'idm'    : connxstr + '/xmlIM/identifier-mgr',
	'stats'  : connxstr + '/xmlIM/stats-mgr',
	'resource' : connxstr + '/xmlIM/resource-mgr',
	'service'  : connxstr + '/xmlIM/service-reg'
}

#
# Get DME handles.  All of them.
#
MH={}
logged_in = 0
for k in UCSVDME:
	try:
		MH[k] = ucsdme(login=user, passwd=password, url=UCSVDME[k])
		logged_in = True
		if options.verbose:
			print "CONNECTED to : ", UCSVDME[k]
	except Exception, e:
		if options.verbose:
			print "Could NOT connect to : ", UCSVDME[k]
		# print str(e)

if not logged_in:
	print
	print "Could not connect. Please make sure the IP and credentials are valid."
	print
	sys.exit(-1)

while 1:
	if not cmd:
		try:
			print "ucsql>> ",
			instring = sys.stdin.readline()
		except KeyboardInterrupt:
			break
		if not instring:
			break
		stmt = instring.rstrip()
		if ( stmt != "" ):
			doStmt( stmt)
		print
	else:
		doStmt (cmd)
		break

for h in MH:
	try:
		MH[h].logout()
	except:
		pass

print
if options.verbose:
		print "\nGood bye"
sys.exit(0)



