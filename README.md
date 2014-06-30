openlearning-offline
====================

Mark and view task submissions offline, and with your text editor!

Requirements
------------

*   Python 2.6+

*   Beautiful Soup 3 (http://www.crummy.com/software/BeautifulSoup/bs3/)
    Install with `pip install BeautifulSoup` or `easy_install BeautifulSoup`

*   An OpenLearning account that can access the marking panel.

### Using at CSE ###

This should work out of the box in the banjo labs at UNSW CSE. I don't know
about other labs.

The login servers don't have Beautiful Soup though, so you'll need to grab
that and put it in the current directoy if you'ved SSH'd in.

How to use
----------

1. Edit config.example as required, and copy to ~/.openlearning/config. The profile name is
   in square brackets. In the example config, this is '1917'.
2. `sudo python setup.py install`
3. `ol.py pull <profile name> <activity>`, eg `ol.py pull 1917 PortfolioMidwayA`
4. Edit `<activity>/<user>/marks` as appropriate.
5. Go into activity dir, and do `ol.py push` as you need. Only marking comments not marked as
   draft will be submitted.

You might also want to view `<activity>/index.html` for submission and marking info.
Use `ol.py index` to rebuild.

Uploading to SMS (UNSW CSE only)
--------------------------------

Once you've finished marking, use `ol-sms.py` in your path (or run it straight
from this folder). 

You need to give it the SMS field name it should upload marks to (eg craft_final).
You can also optionally give it a directory name where it should look for all the 
student submissions.

It will prompt you for your CSE login details. These are not stored.

The script is currently hardcoded for 14s1, and COMP1917. It's unlikely
it'll get used for anything else, except possibly a later session, but
these are easily changed at the top of the script.

Disclaimer
----------

I am sorry to anyone who has to read my terrible code I hacked up this
afternoon. I'll happily accept merge requests to clean it up!

This may violate the OpenLearning Terms of Service. Please consider
before using. If in doubt about your legal situation, seek the advice of
a legal professional. I am not subject to any liabilty for your (mis)use
of this software. See license text below for more information.

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
