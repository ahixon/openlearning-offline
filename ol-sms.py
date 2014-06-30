import urllib
import urllib2
import getpass
import base64
import BeautifulSoup
import sys
import os

COURSE_SESSION = "14s1"
BASE_URL = "https://cgi.cse.unsw.edu.au/~cs1917/%s/tutors/sms.py" % COURSE_SESSION
FETCH_URL = "%s?class=all&weeks=-1" % BASE_URL
OL_FIELD = 'olname'

# returns (fieldname, value) tuple
def get_field_text (field_soup):
    fieldname = field_soup.find ('input')['name']
    value = field_soup.find ('span').text
    return (fieldname, value)

# returns (fieldname, options array, value) tuple
def get_field_enum (field_soup):
    fieldname = field_soup.find ('select')['name']
    options = field_soup.findAll ('option')
    options = map (lambda x: x.string, options)[1:] # first option is always blank
    value = field_soup.find ('span').text
    return (fieldname, options, value)

def main ():
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        sys.stderr.write ("Usage: %s <sms-field-name> [submission-dir]\n" % sys.argv[0])
        sys.exit (1)

    if len(sys.argv) == 2:
        field = sys.argv[1]
        basedir = "."
    else:
        field, basedir = sys.argv[1:]

    # get list of students
    username = raw_input ("Username: ")
    password = getpass.getpass()
    base64_str = base64.encodestring ('%s:%s' % (username, password)).replace('\n', '')

    # ok, let's go
    req = urllib2.Request (FETCH_URL)
    req.add_header ("Authorization", "Basic %s" % base64_str)

    f = urllib2.urlopen (req)
    data = f.read ()
    soup = BeautifulSoup.BeautifulSoup (data)
    if not soup:
        print "Failed to turn page into soup?"
        sys.exit (1)

    mark_table = soup.find ('table')
    rows = mark_table.findAll ('tr')
    fields_row = rows[1]
    fields = map (lambda x: x.string, rows[1].findAll ('th'))
    if field not in fields:
        sys.stderr.write ("Field `%s' is not a valid in SMS. Valid fields are - `%s'\n" % (field, ', '.join (fields)))
        sys.exit (1)

    if OL_FIELD not in fields:
        sys.stderr.write ('%s missing from SMS fields. Name changed, or doesn\'t exist. Aborting.\n' % OL_FIELD)
        sys.exit (1)

    ol_field_index = fields.index (OL_FIELD)
    mark_field_index = fields.index (field)
    zid_index = fields.index ('Student')

    skipped = []
    upload = {} # has of form name: values

    student_marks = rows[2:-1]
    for row in student_marks:
        # make row fields an array
        field_cols = row.findAll ('td')

        # and get olname out
        olfield, olname = get_field_text (field_cols[ol_field_index])
        zid = field_cols[zid_index].text
        subfield, suboptions, subvalue = get_field_enum (field_cols[mark_field_index])

        if not olname:
            print "Missing OpenLearning ID for %s, skipping." % zid
            continue

        # try to open their markfile based on olname
        userdir = os.path.join (basedir, olname)
        if os.path.isdir (userdir):
            if os.path.exists ('%s/.ol_submission' % userdir):
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

                mark = mark_dict['mark'].upper()
                if 'draft' not in mark_dict:
                    #print "Updating %s's mark to %s" % (olname, mark)
                    if mark not in suboptions:
                        print "(!) Mark %s is not a valid SMS mark. Please modify markfile. Ignoring."
                        continue

                    upload[subfield] = mark
                else:
                    print "(!) %s's markfile is still a draft; skipping." % olname
                    skipped.append (subfield)
            else:
                print "Have directory for %s, but no `.ol_submission' file; skipping." % olname
                skipped.append (subfield)
        else:
            print "Missing submission directory for %s; skipping." % olname
            skipped.append (subfield)

    if skipped:
        skip_merge = raw_input ("Would you like to mark all %d skipped entries as AF? " % len(skipped))
        if skip_merge.lower().startswith ('y'):
            for skipkey in skipped:
                upload[skipkey] = 'AF'

    print "Uploading %d entries" % len(upload)

    # don't forget to press the 'Update button', otherwise nothing happens ;)
    upload['Update'] = 'Update'

    post_data = urllib.urlencode (upload)

    # post to endpoint
    req = urllib2.Request (BASE_URL, data=post_data)
    req.add_header ("Authorization", "Basic %s" % base64_str)

    f = urllib2.urlopen (req)
    resp = f.read()

    if 'Confirmed!' in resp:
        print "Success."
    else:
        print "Something bad happened. Here's the raw HTML response:"
        print resp

if __name__ == '__main__':
    main()