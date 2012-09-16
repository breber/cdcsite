__author__ = 'mike.davis'

from google.appengine.ext import db
from google.appengine.ext import blobstore

class Account(db.Model):
    username = db.StringProperty()
    password = db.StringProperty()
    is_admin = db.BooleanProperty()
    is_employee = db.BooleanProperty()
    given_name = db.StringProperty()
    ssn = db.StringProperty()

class Resume(db.Model):
    blob = db.StringProperty()
    given_name = db.StringProperty()
    surname = db.StringProperty()
    email = db.EmailProperty()