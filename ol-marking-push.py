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
		redo[stu['profileName']] = stu

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
		print "Apparently you don't teach any students. Run ./ol-pull-group.sh first?"
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
		print "You have not imported any marks yet."
		return

	taskinfo = open('tasks/%s/taskinfo' % task).read().split('\n')
	activityId, cohortId = taskinfo

	print "Submitting marks for %s..." % task

	marked_users = []
	draft_users = []
	unmarked_users = []

	for username in os.listdir ('tasks/%s/' % task):
		utaskdir = 'tasks/%s/%s' % (task, username)
		if not os.path.isdir (utaskdir):
			continue

		if os.path.exists('%s/marked' % utaskdir):
			marked_users.append (username)
			continue

		if os.path.exists ('%s/mark' % utaskdir):
			marking = open('%s/mark' %utaskdir)
			line = map(str.strip, marking.readline().split (','))
			if 'MARKED' in line:
				print "\tSubmitting marks for %s" % username

				cid = open('%s/contentid' % utaskdir).read().strip()

				# post the comment
				print "\t\tPosting marker comment..."
				content_url = 'https://www.openlearning.com/%s' % cid
				commentpage = opener.open (content_url).read()
				soup = BeautifulSoup.BeautifulSoup(commentpage)
				commentcontainer = soup.find (id='comments-container-main')
				commentdoc = commentcontainer['data-document']

				comment_content =  marking.read()
				comment_content = comment_content.replace ("\n", "<br />")

				export_data = {
					'document': commentdoc,
					'parentComment': '',
					'content': '@%s <br /><br />%s' % (username, comment_content)
				}

				# do some csrf bullshit
				csrf = None
				for cookie in cj:
					#print cookie
					if 'csrf' in cookie.name:
						csrf = cookie.value

				opener.addheaders = [('Referer', content_url),
					('X-CSRFToken', csrf),
					('X-Requested-With', 'XMLHttpRequest')]

				http_data =  urllib.urlencode (export_data.items())
				resp = opener.open ('https://www.openlearning.com/commenting/add/', data=http_data).read()
				jcomment = json.loads (resp)
				if jcomment['success'] != True:
					print "Failed to post marker comment, skipping."
					continue
				

				if not 'NOTICK' in line:
					print "\t\tMarking task as complete..."
					mark_data = {
						'activityId': (activityId),
						'userId': stu[username]['userId'],
						'completed': 'true',
						'cohortId': (cohortId),
						'groupPath': ''
					}

					grade_page = "https://www.openlearning.com/api/mark/?action=setMarkComplete"
					#print grade_page
					http_data =  urllib.urlencode (mark_data.items())
					opener.open (grade_page, data=http_data)
				else:
					print "\t\tNot marking as complete, since task was marked as AF"

				# save local state
				open('%s/marked' % utaskdir, 'w').close()	# mark as marked
				marked_users.append (username)
			elif line:
				draft_users.append (username)
			else:
				unmarked_users.append (username)
		
	print
	print "Marked (%d):" % len(marked_users)
	for u in marked_users:
		print '\t%s' % u

	print "\nDrafts (%d):" % len(draft_users)
	for u in draft_users:
		print '\t%s' % u

	print "\nUnmarked (%d):" % len(unmarked_users)
	for u in unmarked_users:
		print '\t%s' % u

	print "\nTotal: %d submissions (%.2f%% marked)" % (len(marked_users) + len(draft_users) + len(unmarked_users), (float(len(marked_users)) / (len(unmarked_users) + len(marked_users)) * 100))

if __name__ == "__main__":
	main ()
