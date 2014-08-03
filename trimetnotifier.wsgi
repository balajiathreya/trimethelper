#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/trimetnotifier/trimetnotifier/")

from trimetnotifier import app as application
