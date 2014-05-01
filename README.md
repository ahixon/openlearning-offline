openlearning-offline
====================

Mark and view task submissions offline, and with your text editor!

Requirements
------------

* Python 2.6+
* An OpenLearning account that can access the marking panel.

How to use
----------

1) Login to OpenLearning. You only need to do this once.

2) Edit olsettings.py as required. You will need your session ID from your
   browser session.

   It might help if you're set to Remember me when logged in.

3) Run ol-marking-groups.py to fetch student enrollment info from your groups.

4) Run ol-marking-fetch.py <ACTIVITY> to get submissions. You can run this as
   many times as your want, and updated submissions will be downloaded (unless
   you have marked them locally).

   Page submissions will be extracted from the JSON and put into their own HTML
   page.

5) Mark the submissions. You can view the submission in the relevant folder
   under tasks/, and add your comments in 'marks'.

   You can use whatever HTML the comment editor supports.

   When you're done, just make sure the first line of the marking file is
   "MARKED" (without quotes) otherwise the 'push' tool will think you're still
   writing your marking comments and leave them as a draft.

6) Run ol-marking-push.py <ACTIVITY> as you're going along, to upload your
   marking comments and status back to OpenLearning. If you haven't finished 
   marking a student's work, it won't be uploaded.

I am sorry to anyone who has to read my terrible code I hacked up this
afternoon. I'll happily accept merge requests to clean it up!