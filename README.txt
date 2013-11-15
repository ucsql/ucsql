Welcome!

'ucsql' is a new scripting/automation tool that accesses 
the UCS Data Management Engine (DME) using SQL, translated over the XML/API.

Currently 'ucsql' is targeted for customers of UCS Central
who wish to have scripted/automated access for reporting purposes. 

Among the features and benefits of 'ucsql':

-	'ucsql' exploits the common API between UCS Manager and UCS Central: 
  	the same version of 'ucsql' can be used for either/both UCS Manager and UCS Central.
-	'ucsql' has the ability to show/describe the UCS managed object schema, 
	including a list of all available classes, as well as the attributes for a given class, 
	as in "show table".
-	'ucsql' provides "sessions", similar to "goUCS", so that customers can run 
	secure scripted commands, without interactive credential prompting

The 'ucsql' package has the following dependencies:
        - lxml >= 3.2.3         http://lxml.de
        - pyparsing >= 1.5.7    http://pyparsing.wikispaces.com/
        - pycrypto >= 2.6.1     https://www.dlitz.net/software/pycrypto
        - generateDS >= 2.11a   http://www.rexx.com/~dkuhlman/generateDS.html

To install the 'ucsql' package, please type "sudo python setup.py install"

Please refer to the LICENSE.txt file for licensing.

Please refer to the EXAMPLES.txt file for examples.

For questions/discussions, please see http://communities.cisco.com/ucs

This is unsupported Open Source Freeware.  Have Fun, but don't hurt yourself or others.

