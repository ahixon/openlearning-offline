openlearning-offline
====================

Mark and view task submissions offline, and with your text editor!

Requirements
------------

* Python 2.6+
* An OpenLearning account that can access the marking panel.

How to use
----------

1.  Login to OpenLearning. You only need to do this once.

2.  Edit `olsettings.py` as required. You will need your session ID from your
    browser session.

    It might help if you're set to "Remember me" when logged in.

3.  Run `ol-marking-groups.py` to fetch student enrollment info from your
    groups.

4.  Run `ol-marking-fetch.py <ACTIVITY>` to get submissions. You can run this as
    many times as your want, and updated submissions will be downloaded (unless
    you have marked them locally).

    Page submissions will be extracted from the JSON and put into their own HTML
    page.

5.  Mark the submissions. You can view the submission in the relevant folder
    under `tasks/`, and add your comments in `marks`.

    You can use whatever HTML the comment editor supports.

    When you're done, just make sure the first line of the marking file is
    `MARKED` (without quotes) otherwise the 'push' tool will think you're still
    writing your marking comments and leave them as a draft.

6.  Run `ol-marking-push.py <ACTIVITY>` as you're going along, to upload your
    marking comments and status back to OpenLearning. If you haven't finished 
    marking a student's work, it won't be uploaded.

Disclaimer
----------

I am sorry to anyone who has to read my terrible code I hacked up this
afternoon. I'll happily accept merge requests to clean it up!

License
-------

The MIT License (MIT)

Copyright (c) 2014 Alex Hixon <alex@alexhixon.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.