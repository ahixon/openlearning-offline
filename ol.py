#!/usr/bin/env python
import sys
import os
import ConfigParser
from olweb import OLWeb
import getpass
import json
import time, datetime
import glob

#from pkg_resources import resource_filename

user_config = None
current_course = None

def login_handler ():
    username = user_config.get (current_course, 'username')
    print "Username: %s" % username
    password = getpass.getpass()
    return (username, password)

def get_students (ol, groups_dir, group_list, force_sync=False):
    students = []

    for group in group_list:
        group_filename = os.path.join (groups_dir, group)
        if not os.path.isfile (group_filename) or force_sync:
            print "Getting group `%s' members..." % group
            data = ol.get_group_json (group)
            if not data:
                print "No such group `%s', or OpenLearning failed to give us correct data." % group
                sys.exit (1)
            
            with open (group_filename, 'wb') as f:
                f.write (json.dumps (data))

            for stu in data:
                stu['group'] = group

            students.extend (data)
        else:
            with open(group_filename) as f:
                data = json.loads (f.read())
                for stu in data:
                    stu['group'] = group

                students.extend (data)

    return students

def get_uid_map (students):
    redo = {}
    for stu in students:
        redo[stu['userId']] = stu

    return redo

def fetch_submission (web, activity_name, submission_info, user_info, path):
    if not os.path.isdir (path):
        os.mkdir (path)

    submission_json = web.get_submission (submission_info['contentid'])
    saved = open('%s/submission.json' % path, 'w')
    saved.write(json.dumps (submission_json))
    saved.close()

    submission_config = ConfigParser.RawConfigParser()
    submission_config.add_section ('user')
    submission_config.set ('user', 'name', user_info['fullName'])
    submission_config.set ('user', 'nick', user_info['profileName'])
    submission_config.set ('user', 'id', user_info['userId'])   # FIXME: normalise pls

    submission_config.add_section ('submission')
    submission_config.set ('submission', 'cohort_id', submission_info['cohortid'])
    submission_config.set ('submission', 'activity_id', submission_info['activityid'])
    submission_config.set ('submission', 'activity_name', activity_name)
    submission_config.set ('submission', 'content_id', submission_info ['contentid'])
    submission_config.set ('submission', 'time', int(time.mktime(submission_info['time'].timetuple())))

    with open('%s/%s' % (path, '.ol_submission'), 'wb') as configfile:
        submission_config.write (configfile)

    htmlExportPath = None
    if submission_json['submission']['content']['pageType'] == 'html':
        # export to html
        htmlExportPath = "%s/submission.html" % path

        html = open(htmlExportPath, 'w')
        html.write('<html><head><meta charset="UTF-8"></head><body>')
        html.write(submission_json['submission']['content']['pageHTML'].encode('utf8'))
        html.write('</body></html>')
        html.close()

    if not os.path.isfile ('%s/marks' % path):
        markfile = open('%s/marks' % path, 'wb')
        markfile.write ("mark=??, draft\nYour comments go here. Delete the 'draft' keyword when you're done.")
        markfile.close()

    # FIXME: add late info to actual submission page

    return htmlExportPath

def get_mark (dir):
    try:
        markfile = open (os.path.join (dir, 'marks'))
        tags = map (str.strip, markfile.readline().lower().split (','))
        mark = "??"
        for tag in tags:
            if '=' in tag:
                key, value = tag.split('=')
                if key == 'mark':
                    mark = value
                    break

        return ('draft' in tags, mark.upper())
    except:
        return (True, '??')

from collections import defaultdict

def median(mylist):
    sorts = sorted(mylist)
    length = len(sorts)
    if not length % 2:
       return (sorts[length / 2] + sorts[length / 2 - 1]) / 2.0
    return sorts[length / 2]

def average (l):
    return float(sum(l))/len(l) if len(l) > 0 else float('nan')

def generate_index (basedir, task, activity_config, user_config, groups_dir, ol_dir):
    # generate new HTML page
    try:
        due_date = datetime.datetime.fromtimestamp (activity_config.getfloat ('activity', 'due'))
    except:
        due_date = None

    seen_students = []

    current_course = activity_config.get('activity', 'usercourse')
    cohort = user_config.get(activity_config.get('activity', 'usercourse'), 'cohort')
    course = user_config.get(activity_config.get('activity', 'usercourse'), 'course')
    
    web = OLWeb (cohort, course, os.path.join(ol_dir, '.ol_cookies_' + current_course), login_handler)
    group_list = user_config.get(activity_config.get('activity', 'usercourse'), 'groups')
    group_list = map(str.strip, group_list.split(','))
    students = get_students (web, groups_dir, group_list)
    students_hash = get_uid_map (students)

    index = "<html><head><title>Submissions for %s</title>" % task
    index += "<style>"
    index += "body { background-color: #3a3b39; color: #fff } a { color: #eeeeec; } "
    index += "table { border-collapse:collapse; cell-padding: 6px; } td,th { padding: 0.4em }"
    index += "</style>"
    index += "</head><body><h1>Submissions for %s</h1>" % (task)
    index += "<table><tr><th>Name</th><th>Group</th><th>Submission</th><th>Due date delta</th><th></th><th>Mark</th><th>OL upload</th><th>SMS upload</tr>"

    scoreListNum = []
    scoreListStr = []

    # should give compressed gumleaf?
    scores = {
        'HD': 85.0,
        'DN': 75.0,
        'CR': 65.0,
        'PS': 50.0,
        'PC': 46.0,
        'FL': 0.0,
    }

    for sub in glob.glob (os.path.join (basedir, '*/submission.html')):
        link = sub.replace (basedir, '.')
        userdir = os.path.sep.join (sub.split (os.path.sep)[:-1])

        submission_info = ConfigParser.RawConfigParser()
        submission_data_path = os.path.join (userdir, '.ol_submission')
        submission_info.read (submission_data_path)

        delta = "Please set activity due date in <code>.ol_activity</code>."
        if due_date is not None:
            submission_time = datetime.datetime.fromtimestamp (submission_info.getfloat ('submission', 'time'))
            delta = submission_time - due_date
            if delta > datetime.timedelta (days=1):
                deltaStyle = "red"
            elif delta > datetime.timedelta (minutes=5):
                deltaStyle = "orange"
            elif delta > datetime.timedelta (seconds=0):
                deltaStyle = "yellow"
            elif delta < datetime.timedelta (days=1):
                deltaStyle = "green; color: white"
            elif delta < datetime.timedelta (minutes=5):
                deltaStyle = "lightgreen"
            else:
                deltaStyle = "grey"
        else:
            deltaStyle = 'white; font-weight: bold'


        draft, mark = get_mark (userdir)
        markStr = str(mark)

        markColors = {
            'HD': 'green',
            'DN': 'lightgreen; color: black',
            'CR': 'grey',
            'PS': 'purple',
            'PC': 'orange',
            'FL': 'red',
            'AF': 'black',
            '??': ''
        }

        if mark != 'AF' and mark != '??':
            scoreListStr.append (mark)
            scoreListNum.append (scores[mark])

        markStyle = markColors[mark]
        if draft:
            edit = "&#9998;"
        else:
            edit = ""

        if submission_info.has_option ('submission', 'marked'):
            uploaded_ol = "&#10004;"
            uploaded_ol_style = "background-color: green;"
        else:
            uploaded_ol = ""
            uploaded_ol_style = ""

        online_link = 'https://www.openlearning.com/content/%s' % submission_info.get ('submission', 'content_id')
        group = students_hash[submission_info.get ('user', 'id')]['group']
        index += "<tr><td>%s</td><td>%s</td><td><a href='%s'>Local</a>, <a href='%s'>Online</a></td><td style='background-color: %s'>%s</td><td>%s</td><td style='background-color: %s'>%s</td><td style='text-align: center; %s'>%s</td><td></td></tr>" % (submission_info.get ('user', 'name'), group, link, online_link, deltaStyle, delta, edit, markStyle, markStr, uploaded_ol_style, uploaded_ol)

        seen_students.append (submission_info.get ('user', 'id'))

    # now do everyone who didn't submit stuff

    for student in students:
        if student['userId'] not in seen_students:
            if datetime.datetime.now() > due_date:
                bad = "background-color: red"
            else:
                bad = ""
            index += "<tr><td>%s</td><td>%s</td><td></td><td style='%s'>No submission</td><td></td><td></td><td></td><td></td></tr>" % (student['fullName'], student['group'], bad)

    if scoreListNum:
        index += "<tr><td colspan='6' align='right'><b>Average of %d:</b></td><td><b>%.2f</b></td></tr>" % (len (scoreListNum), average (scoreListNum))
        index += "<tr><td colspan='6' align='right'><b>Median of %d:</b></td><td><b>%s</b></td></tr>" % (len (scoreListNum), median (scoreListNum))

    index += "</table>"
    index += "<p><small>Generated at %s</small></p>" % datetime.datetime.now()
    index += "</html>"

    html = open ('%s/index.htm' % basedir, 'wb')
    html.write (index)
    html.close()

def push_activity (ol_dir, activity_config, user_config, basedir, groups_dir):
    global current_course

    current_course = activity_config.get('activity', 'usercourse')
    cohort = user_config.get(activity_config.get('activity', 'usercourse'), 'cohort')
    course = user_config.get(activity_config.get('activity', 'usercourse'), 'course')
    
    web = OLWeb (cohort, course, os.path.join(ol_dir, '.ol_cookies_' + current_course), login_handler)
    group_list = user_config.get(activity_config.get('activity', 'usercourse'), 'groups')
    group_list = map(str.strip, group_list.split(','))

    activity_name = activity_config.get('activity', 'name')
    activities = None

    if not activity_config.has_option ('activity', 'valid'):
        print "Invalid activity. Try to pull."
        sys.exit(1)

    students = get_students (web, groups_dir, group_list)
    uid_map = get_uid_map (students)

    for username in os.listdir (basedir):
        userdir = os.path.join (basedir, username)
        if os.path.isdir (username):
            if os.path.exists ('%s/.ol_submission' % userdir):
                submission_config = ConfigParser.RawConfigParser()
                submission_config.read ('%s/.ol_submission' % userdir)

                if not submission_config.has_option ('submission', 'marked'):
                    # check markfile to see if we're still draft
                    markfile = open('%s/marks' % userdir)
                    mark_tags = map(str.strip, markfile.readline().lower().split (','))

                    mark_dict = {}

                    for tag in mark_tags:
                        if '=' in tag:
                            tag = tag.split('=')
                            mark_dict[tag[0]] = tag[1]
                        else:
                            mark_dict[tag] = True

                    if 'draft' not in mark_dict:
                        print "Submitting mark for %s..." % submission_config.get ('user', 'name')
                        print "\tPosting comment..."

                        # tag student
                        comment_content = '@%s\n\n' % submission_config.get ('user', 'nick')

                        # attach marker comment
                        comment_content += markfile.read()

                        # append mark info
                        if 'mark' in mark_dict:
                            comment_content += "\n\nFinal mark: %s" % mark_dict['mark'].upper()
                        else:
                            comment_content += "\n\nNo final mark given."

                        #print comment_content

                        # new lines get replaced with line breaks inside post_comment
                        if not web.post_comment (submission_config.get ('submission', 'content_id'), comment_content):
                            print "\tPosting comment failed, skipping"
                            continue

                        print "\tMarking as complete..."
                        web.tick_activity (submission_config.get ('submission', 'activity_id'),
                            submission_config.get ('user', 'id'),
                            submission_config.get ('submission', 'cohort_id'))

                        submission_config.set ('submission', 'marked', 'true')

                        with open('%s/%s' % (userdir, '.ol_submission'), 'wb') as configfile:
                            submission_config.write (configfile)
                            
    generate_index (basedir, activity_name, activity_config, user_config, groups_dir, ol_dir)

def page_print (pg):
    print "[*] Loading page %d..." % pg

def pull_activity (ol_dir, activity_config, user_config, basedir, groups_dir):
    global current_course

    current_course = activity_config.get('activity', 'usercourse')
    cohort = user_config.get(activity_config.get('activity', 'usercourse'), 'cohort')
    course = user_config.get(activity_config.get('activity', 'usercourse'), 'course')
    
    web = OLWeb (cohort, course, os.path.join(ol_dir, '.ol_cookies_' + current_course), login_handler)
    group_list = user_config.get(activity_config.get('activity', 'usercourse'), 'groups')
    group_list = map(str.strip, group_list.split(','))

    activity_name = activity_config.get('activity', 'name')
    activities = None

    if not activity_config.has_option ('activity', 'valid'):
        # Dear OpenLearning, USE HTTP STATUS CODES, YA KNOW, FOR LIKE, PAGES THAT AREN'T FOUND.
        # Love, Alex.

        # XXX: hack because we only want to one-shot this and get_submissions shouldn't do this each call
        activities = web.get_activities()
        activity_dates = next ((x for x in activities if x['slug'] == activity_name), None)

        if activity_dates is None:
            activity_config.set ('activity', 'valid', 'false')
        else:
            activity_config.set ('activity', 'valid', 'true')
            activity_config.set ('activity', 'due', int(time.mktime(activity_dates['endDate'].timetuple())))

        with open('%s/%s' % (basedir, '.ol_activity'), 'wb') as configfile:
            activity_config.write (configfile)

    if activity_config.getboolean ('activity', 'valid') == False:
        sys.stderr.write ("Error: no such activity `%s' in course `%s'.\n"
            "Check the name and edit `.ol_activity', or add the activity to your course.\n" % (activity_name, course))
        sys.stderr.write ("You can run ./ol.py activities to get a valid list of activities.")

        sys.exit (1)

    if not activity_config.has_option ('activity', 'latest'):
        latest = datetime.datetime.fromtimestamp (0)
    else:
        latest = datetime.datetime.fromtimestamp (activity_config.getint ('activity', 'latest'))

    students = get_students (web, groups_dir, group_list)
    uid_map = get_uid_map (students)

    # loop over all submissions we have
    new_latest = datetime.datetime.now()
    for submission in web.get_submissions (activity_name, page_callback=page_print):
        if not activity_config.has_option ('activity', 'cohortid'):
            activity_config.set('activity', 'cohortid', submission['cohortid'])
            activity_config.set('activity', 'activityid', submission['activityid'])

            with open('%s/%s' % (basedir, '.ol_activity'), 'wb') as configfile:
                activity_config.write (configfile)

        if submission['time'] <= latest:
            # old submission, stop searching
            print "Up to date."
            break

        # get submission content
        if submission['userid'] in uid_map:
            user_info = uid_map[submission['userid']]

            checkout_dir = os.path.join (basedir, user_info['profileName'])
            submission_data_path = os.path.join (checkout_dir, '.ol_submission')
            if os.path.exists (submission_data_path):
                submission_info = ConfigParser.RawConfigParser()
                submission_info.read (submission_data_path)
                submission_time = datetime.datetime.fromtimestamp (submission_info.getfloat ('submission', 'time'))

                if submission_time >= submission['time']:
                    #print "\tskipping, had newer"
                    continue

            print "    Fetching submission from", user_info['fullName']
            fetch_submission (web, activity_name, submission, user_info, checkout_dir)

    generate_index (basedir, activity_name, activity_config, user_config, groups_dir, ol_dir)
    
    activity_config.set ('activity', 'latest', int(time.mktime(new_latest.timetuple())))
    with open('%s/%s' % (basedir, '.ol_activity'), 'wb') as configfile:
        activity_config.write (configfile)

## BIG ASS TODO: make these functions generic enough so that we can pass in any environment
## and the operation should work regardless (ie a user dir vs a whole activity)
## ALSO: need to hide all this 'config' yuckiness into a class or something.
def main ():
    global user_config      # FIXME: this needs to go - see above.

    # FIXME: see above.
    if len(sys.argv) < 2 or not ((sys.argv[1] == 'pull' and (len(sys.argv) == 4 or len(sys.argv) == 2)) or len(sys.argv) == 2):
        sys.stderr.write ('Usage: %s pull|pull <course> <activity>|activities|push|index\n' % sys.argv[0])
        sys.exit(1)

    sys.argv = sys.argv[1:]

    ol_dir = os.path.expanduser ('~/.openlearning/')
    if not os.path.isdir (ol_dir):
        os.mkdir (ol_dir)

    groups_dir = os.path.join (ol_dir, 'groups')
    if not os.path.isdir (groups_dir):
        os.mkdir (groups_dir)

    user_config = ConfigParser.RawConfigParser()
    user_config_path = os.path.join (ol_dir, 'config')
    if not os.path.exists (user_config_path):
        sys.stderr.write ('You have no OpenLearning configuration. Please edit %s.\n' % user_config_path)
        sys.exit(1)

    user_config.read (user_config_path)

    config = ConfigParser.RawConfigParser()

    if sys.argv[0] == 'pull' and len(sys.argv) == 1:
        if not os.path.isfile ('.ol_activity'):
            sys.stderr.write ('This folder is not an OpenLearning activity. Change directory, or use `pull <course> <activity>`.\n')
            sys.exit (1)

        config.read ('.ol_activity')
        pull_activity (ol_dir, config, user_config, '.', groups_dir)
    elif sys.argv[0] == 'pull':
        usercourse, activity = sys.argv[1:]

        if not user_config.has_section (usercourse):
            sys.stderr.write ("No such course `%s' defined in %s.\n" % (usercourse, user_config_path))
            sys.exit (1)

        # create a new activity folder
        if not os.path.exists ('%s/.ol_activity' % activity):
            print "Pulling into `%s'..." % activity

            if not os.path.exists (activity):
                os.mkdir (activity)

            config = ConfigParser.RawConfigParser()

            config.add_section ('activity')
            config.set('activity', 'name', activity)
            config.set('activity', 'usercourse', usercourse)

            with open('%s/%s' % (activity, '.ol_activity'), 'wb') as configfile:
                config.write (configfile)

        else:
            config.read ('%s/.ol_activity' % activity)

        pull_activity (ol_dir, config, user_config, activity, groups_dir)
    elif sys.argv[0] == 'activities':
        user_course = "1917"

        cohort = user_config.get(user_course, 'cohort')
        course = user_config.get(user_course, 'course')
        
        web = OLWeb (cohort, course, os.path.join(ol_dir, '.ol_cookies_' + user_course), login_handler)

        activities = web.get_activities()
        for act in activities:
            sys.stderr.write ("%s\n" % act['slug'])
    elif sys.argv[0] == 'push':
        if not os.path.isfile ('.ol_activity'):
            sys.stderr.write ('This folder is not an OpenLearning activity. Change directory, or use `push <course> <activity>`.\n')
            sys.exit (1)

        config.read ('.ol_activity')
        push_activity (ol_dir, config, user_config, '.', groups_dir)
    elif sys.argv[0] == 'index':
        basedir = '.'
        config.read ('%s/.ol_activity' % basedir)
        generate_index (basedir, config.get ('activity', 'name'), config, user_config, groups_dir, ol_dir)
    else:
        sys.stderr ("Unknown command `%s'.", sys.argv[0])

if __name__ == '__main__':
    main ()
