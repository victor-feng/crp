# -*- coding: utf-8 -*-
from flask_mongoengine import MongoEngine

# MongoEngine Support UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

db = MongoEngine()


class User(db.Document):
    email = db.StringField(required=True)
    first_name = db.StringField(max_length=50)
    last_name = db.StringField(max_length=50)
