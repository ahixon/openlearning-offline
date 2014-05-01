import urllib
import urllib2
import json
import time
import sys
import os
import cookielib
import csv
import datetime

import olsettings

def main ():
	SESSIONID = olsettings.SESSIONID
	if not SESSIONID:
		print "No session ID set - please edit olsettings.py"
		return

	cj = cookielib.CookieJar()
	cj.set_cookie (cookielib.Cookie (version=0, name='sessionid', value=SESSIONID, port=None, port_specified=False, domain='www.openlearning.com', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=True, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False))
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

	if not os.path.isdir ('groups/'):
		os.mkdir ('groups')

	for gname in olsettings.GROUPS:
		print "Fetching group", gname
		prev_page = "https://www.openlearning.com/data/group/?groupPath=courses/%s/Cohorts/%s/Groups/%s" % (olsettings.COURSE_NAME, olsettings.COHORT, gname)
		f = opener.open (prev_page)

		content = f.read()
		f.close()

		gdump = open('groups/%s' % gname, 'w')
		gdump.write(content)
		gdump.close()

if __name__ == "__main__":
	main()