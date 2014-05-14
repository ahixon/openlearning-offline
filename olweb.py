import json
import BeautifulSoup
import urllib2
import cookielib
import urllib
import time
import datetime

class ScrapeError (Exception):
    def __init__ (self, url, orig_exception):
        self.ex = orig_exception
        self.url = url

    def __str__ (self):
        return 'Could not find expected elements on page %s - perhaps layout has changed?: %s' % (self.url, self.ex)


class ForbiddenError (Exception):
    pass

class OLWeb(object):
    def __init__ (self, cohort, course_name, cookie_file=None, login_handler=None):
        if cookie_file:
            self.cj = cookielib.LWPCookieJar (cookie_file)
            try:
                self.cj.load (cookie_file)
            except IOError:
                pass
        else:
            self.cj = cookielib.CookieJar ()

        self.opener = urllib2.build_opener (urllib2.HTTPCookieProcessor (self.cj))
        self.login_handler = login_handler
        self.cohort = cohort
        self.course_name = course_name

    def _get_beautiful_page (self, url):
        return BeautifulSoup.BeautifulSoup (str(self.get_page_content (url)))

    def get_content (self, contentid):
        return self.get_page_content ('https://www.openlearning.com/content/%s' % contentid)

    def _get_json (self, url):
        return json.loads (self.get_page_content (url))

    def _get_beautiful_content (self, contentid):
        return BeautifulSoup.BeautifulSoup (str(self.get_content(contentid)))

    def get_page_content (self, url):
        bad_permissions = False

        try:
            content = self.opener.open (url).read()
        except urllib2.HTTPError, ex:
            if ex.code == 401:
                bad_permissions = True
                content = ''
            else:
                raise ex

        if 'registrationForm' in content or bad_permissions:
            logged_in = False
            while not logged_in:
                # FIXME: do we need csrfmiddlewaretoken?
                # can't use get_* here because they call this function, so:
                net = self.opener.open ('https://www.openlearning.com/accounts/login/')
                soup = BeautifulSoup.BeautifulSoup (str(net.read()))
                try:
                    html_token = soup.find ('input', {'name': 'csrfmiddlewaretoken'})
                    token = html_token['value']
                except Exception, ex:
                    raise ScrapeError (url, ex)

                if not self.login_handler:
                    raise ForbiddenError (url)

                username, password = self.login_handler ()

                result = self.post_to ('https://www.openlearning.com/accounts/login/', {
                    'username': username,
                    'password': password,
                    'csrfmiddlewaretoken': token,
                    'redirectTo' : ''
                })

                logged_in = 'registrationForm' not in result

            # try to get page again
            self.cj.save(ignore_expires=True)
            return self.get_page_content (url)

        self.cj.save(ignore_expires=True)
    	return content

    def post_to (self, url, post_dict):
        # do some csrf bullshit
        csrf = None
        for cookie in self.cj:
            if 'csrf' in cookie.name:
                csrf = cookie.value

        self.opener.addheaders = [('Referer', url),
            ('X-CSRFToken', csrf),
            ('X-Requested-With', 'XMLHttpRequest')]

        post_data = urllib.urlencode (post_dict.items())
        result = self.opener.open (url, data=post_data).read()
        return result
    
    def post_to_json (self, url, post_dict):
        resp = self.post_to (url, post_dict)
        jcomment = json.loads (resp)
        return jcomment['success']

    def post_comment (self, contentid, comment, in_reply_to=''):
        page = self._get_beautiful_content (contentid)

        try:
            html_container = page.find (id='comments-container-main')
            comment_docid = html_container['data-document']
        except Exception, ex:
            raise ScrapeError (contentid, ex)

        comment = comment.replace ("\n", "<br />")

        post_data = {
            'document': comment_docid,
            'parentComment': in_reply_to,
            'content': comment
        }

        return self.post_to_json ('https://www.openlearning.com/commenting/add/', post_data)

    def get_activity_path (self, task):
        return 'courses/%s/Activities/%s' % (self.course_name, task)

    def get_cohort_path (self):
        return 'courses/%s/Cohorts/%s' % (self.course_name, self.cohort)

    def get_submission (self, contentid): 
        return self._get_json ("https://www.openlearning.com/api/submissions/page/content/%s" % contentid)

    """
    Returns an iterator over all the submissions for a particular activity.
    """
    def get_submissions (self, activity=''):
        page = 1
        had_submissions = True
        while had_submissions:
            had_submissions = False
            url = "https://www.openlearning.com/marking?activity=%s&cohort=%s&page=%d" % (
                self.get_activity_path (activity), self.get_cohort_path (), page)

            soup = self._get_beautiful_page (url)

            try:
                markTable = soup.find(id='markingTable')
                rows = markTable.findAll('tr')
                for row in rows:
                    ucol = row.find ('td', {'class': 'nameCell'})
                    if ucol:
                        uid = ucol['data-userid']
                        had_submissions = True

                        groupname = ucol['data-grouppath'] or None
                        if groupname:
                            groupname = groupname.split('/')[-1]

                        subtimerow = row.find ('td', {'class': 'submissionTimeCell'})
                        subtimestr = subtimerow.string.strip()
                        try:
                            subtime = datetime.datetime.strptime (subtimestr, "%Y-%m-%dT%H:%M:%S.%fZ")
                        except ValueError:
                            # try without milliseconds (thanks Randal)
                            subtime = datetime.datetime.strptime (subtimestr, "%Y-%m-%dT%H:%M:%SZ")

                        sublink = row.find ('td', {'class' : 'submissionLinkCell'})
                        sublink = sublink.find ('a')
                        contentid = sublink['href'].split('?')[0].split('/')[-1]

                        activityrow = row.find ('td', {'class': 'activityCell'})
                        activityid = activityrow['data-activityid']

                        cohortrow = row.find ('td', {'class': 'courseCell'})
                        cohortid = cohortrow['data-cohortid']


                        submission = {
                            'userid': uid,
                            'time': subtime,
                            'contentid': contentid,

                            # if you want to mark this off, you need to keep this
                            'activityid': activityid,
                            'cohortid': cohortid
                        }

                        yield submission

                page += 1

            except Exception, ex:
                raise ScrapeError (url, ex)

    def _fix_activity (self, obj):
        obj['slug'] = obj['link'].split('/')[-1]

        timestr = obj['endDate']
        try:
            obj['endDate'] = datetime.datetime.strptime (timestr, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            obj['endDate'] = datetime.datetime.strptime (timestr, "%Y-%m-%dT%H:%M:%SZ")

        timestr = obj['startDate']
        try:
            obj['startDate'] = datetime.datetime.strptime (timestr, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            obj['startDate'] = datetime.datetime.strptime (timestr, "%Y-%m-%dT%H:%M:%SZ")

        return obj

    def get_activities (self):
        dates = self._get_json ('https://www.openlearning.com/api/cohort/dates?cohort=courses/%s/Cohorts/%s' % (self.course_name, self.cohort))

        # FIXME: wtf? it's encoded as a string again?
        dates = json.loads(dates['cohortDates'])
        
        # TODO: we might want module dates too
        acts = []
        for module in dates['modules']:
            acts.extend (map (lambda y: OLWeb._fix_activity(self, y), module['activities']))

        return acts

    def get_group_json (self, groupname):
        return self._get_json ("https://www.openlearning.com/data/group/?groupPath=courses/%s/Cohorts/%s/Groups/%s" % (self.course_name, self.cohort, groupname))


    def tick_activity (self, activity_id, user_id, cohort_id):
        mark_data = {
            'activityId': activity_id,
            'userId': user_id,
            'completed': 'true',
            'cohortId': cohort_id,
            'groupPath': ''
        }

        return self.post_to_json ("https://www.openlearning.com/api/mark/?action=setMarkComplete", mark_data)