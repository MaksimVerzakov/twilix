import time
import hashlib
import random

def genSID():
    sid = unicode(time.time())
    sid += unicode(random.random())
    return hashlib.sha1(sid).hexdigest()
