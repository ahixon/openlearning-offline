import urllib
import urllib2
import json
import time
import sys
import os
import cookielib
import csv
import BeautifulSoup
import datetime

import olsettings

SESSIONID = None
"""
def make_ol_request (url):
	global SESSIONID
	req = urllib2.Request(url)
	print "SESSIONID = ", SESSIONID
	req.add_header('Cookie', 'sessionid="%s"' % (urllib.quote_plus(SESSIONID)))
	return req
"""

def read_json (f):
	#f = opener.open(req)
	return json.loads (f.read ())

def get_students ():
	students = []
	for fn in os.listdir ('groups/'):
		f = open('groups/%s' % fn)
		js = json.loads (f.read ())
		students.extend (js)
		f.close ()

	return students

def get_profile_names (students):
	#return map (lambda x: x['profileName'], students)
	redo = {}
	for stu in students:
		redo[stu['userId']] = stu

	return redo

def main ():
	global SESSIONID
	if len(sys.argv) != 2:
		print "Usage: %s <ACTIVITY_NAME>" % sys.argv[0]
		return

	SESSIONID = olsettings.SESSIONID
	task = sys.argv[1]

	# check if we have the user lists
	stu = get_students ()
	if not stu:
		print "Apparently you don't teach any students. Run ./ol-marking-groups.py first?"
		return

	# filter to array
	stu = get_profile_names (stu)

	cj = cookielib.CookieJar()
	#version=0, name='Name', value='1', port=None, port_specified=False, domain='www.example.com', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False
	#cj.set_cookie (cookielib.Cookie (name='sessionid', value=SESSIONID))
	cj.set_cookie (cookielib.Cookie (version=0, name='sessionid', value=SESSIONID, port=None, port_specified=False, domain='www.openlearning.com', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=True, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False))
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

	#print "Getting CSRF param..."

	cohort_url = 'courses/%s/Cohorts/%s' % (olsettings.COURSE_NAME, olsettings.COHORT)
	activity_url = 'courses/%s/Activities/%s' % (olsettings.COURSE_NAME, task)


	if not os.path.isdir ('tasks/%s' % task):
		os.makedirs ('tasks/%s' % task)

	export_data = {
		'cohort': cohort_url,
		'activity': activity_url
	}

	print "Exporting marks for %s..." % task

	had_stuff = True
	page = 1

	while had_stuff:
		had_stuff = False
		print "Loading page %d" % page
		prev_page = "https://www.openlearning.com/marking?activity=%s&cohort=%s&page=%d" % (activity_url, cohort_url, page)
		f = opener.open (prev_page)

		content = f.read()
		f.close()

		soup = BeautifulSoup.BeautifulSoup (content)
		markTable = soup.find(id='markingTable')
		rows = markTable.findAll('tr')
		for row in rows:
			ucol = row.find ('td', {'class': 'nameCell'})
			if ucol:
				uid = ucol['data-userid']
				had_stuff = True

				if uid in stu:
					stuname = stu[uid]['profileName']
					print "Fetching submission for %s..." % stu[uid]['fullName']

					subtimerow = row.find ('td', {'class': 'submissionTimeCell'})
					subtimestr = subtimerow.string.strip()
					try:
						subtime = datetime.datetime.strptime (subtimestr, "%Y-%m-%dT%H:%M:%S.%fZ")
					except ValueError:
						# try without milliseconds (thanks Randal)
						subtime = datetime.datetime.strptime (subtimestr, "%Y-%m-%dT%H:%M:%SZ")

					sublink = row.find ('td', {'class' : 'submissionLinkCell'})
					sublink = sublink.find ('a')
					contentid = sublink['href'].split('?')[0]

					activityrow = row.find ('td', {'class': 'activityCell'})
					activityid = activityrow['data-activityid']

					cohortrow = row.find ('td', {'class': 'courseCell'})
					cohortid = cohortrow['data-cohortid']

					if not os.path.exists ('tasks/%s/taskinfo' % task):
						ti = open('tasks/%s/taskinfo' % task, 'w')
						ti.write ('%s\n%s' % (activityid, cohortid))
						ti.close()

					studir = 'tasks/%s/%s' % (task, stuname)
					if not os.path.isdir (studir):
						os.mkdir (studir)

					if os.path.exists ('%s/current' % studir):
						cf = open('%s/current' % studir)
						current_disk = cf.read().strip()
						try:
							current_disk = datetime.datetime.strptime (current_disk, "%Y-%m-%dT%H:%M:%S.%fZ")
						except ValueError:
							current_disk = datetime.datetime.strptime (current_disk, "%Y-%m-%dT%H:%M:%SZ")
						cf.close ()
					else:
						current_disk = datetime.datetime.min

					if current_disk < subtime and not os.path.exists ('%s/mark_sent' % studir):
						print "Downloading new submission..."
						# fetch it

						contentpage = "https://www.openlearning.com/api/submissions/page/%s" % contentid
						print contentpage
						submission = opener.open (contentpage).read()
						saved = open('%s/submission.json' % studir, 'w')
						saved.write(submission)
						saved.close()

						submission = json.loads(submission)
						if submission['submission']['content']['pageType'] == 'html':
							# export to html
							html = open('%s/submission.html' % studir, 'w')
							html.write('<html><head><meta charset="UTF-8"></head><body>')
							html.write(submission['submission']['content']['pageHTML'].encode('utf8'))
							html.write('</body></html>')
							html.close()

						# and update timestamps
						cf = open('%s/current' % studir, 'w')
						cf.write (subtimestr)
						cf.close()

						cf = open('%s/contentid' % studir, 'w')
						cf.write (contentid)
						cf.close()

						# touch the marking comments file
						open ('%s/mark' % studir, 'w')
					else:
						print "Skipping download; we already have the latest version."

					

		page += 1

	print "All submissions fetched."
	print
	print "To mark, edit each 'mark' file with your comments."
	print "Once done, add the word MARKED at the top of the file - only then will it be submitted when you use ol-marking-push.py"

if __name__ == "__main__":
	main ()
