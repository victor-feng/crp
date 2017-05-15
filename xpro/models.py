# _*_coding:utf-8_*_
# from django.db import models
#
# Create your models here.
import sys

local_dir = './'
sys.path.append(local_dir)
from mongoengine import (DateTimeField,
                         DynamicDocument, StringField, EmbeddedDocumentField,
                         EmbeddedDocument, ListField, NotUniqueError)
import datetime
from mongoengine import connect

connect('cmdb', host='mongodb://172.28.20.124/cmdb', username='cmdb', password='cmdb')


class RepoItemString(EmbeddedDocument):
    """
    单行文本
    """

    name = StringField(required=True)
    p_code = StringField(required=False)
    default_value = StringField(max_length=50, required=False)
    created_time = DateTimeField(default=datetime.datetime.now())
    meta = {
        "collection": "cmdb_string",
        "index": [
            {
                'fields': ["name", "p_code"],
                'unique': True,
                # 'null': True,
            }
        ],
        'index_background': True
    }


class RepoItemInt(EmbeddedDocument):
    """
    整数
    """
    name = StringField(required=True)
    p_code = StringField(required=False)
    default_value = StringField(required=False)
    unit = StringField(required=False)  # 单位
    created_time = DateTimeField(default=datetime.datetime.now())

    meta = {
        "collection": "cmdb_select",
        "index": [
            {
                "fields": ["name", "p_code"],
                "unique": True,
            }
        ],
    }


class RepoItemDatetime(EmbeddedDocument):
    """
    日期时间
    """
    name = StringField(required=True)
    p_code = StringField(required=False)
    default_value = StringField()

    meta = {
        "collection": "cmdb_date",
        "index": [
            {
                "fields": ["name", "p_code"],
                "unique": True,
            }
        ],
    }


class RepoItem(DynamicDocument):
    """
    对象
    """
    name = StringField(required=True, unique=True)
    p_code = StringField(required=True, unique=True)
    layer = StringField(required=True)
    group = StringField(required=True)
    item = StringField(required=True)
    repoitem_string = ListField(EmbeddedDocumentField('RepoItemString'))
    # repoitem_choice = ListField(EmbeddedDocumentField('RepoItemChoice'))
    # repoitem_multiselect = ListField(EmbeddedDocumentField('RepoItemMultiselect'))
    repoitem_datetime = ListField(EmbeddedDocumentField('RepoItemDatetime'))
    repoitem_int = ListField(EmbeddedDocumentField('RepoItemInt'))
    created_time = DateTimeField(default=datetime.datetime.now())

    # 祖先数组
    ancestors = ListField(StringField())
    parent = StringField()
    meta = {
        'collection': 'repo_item',
        'index': [
            {
                'fields': ['name', 'p_code', 'ancestors'],
                # 'unique': True,
                'sparse': True,
            }
        ],
        'index_background': True
    }

    @classmethod
    def created_repoitem(cls, name, p_code, layer_id, group_id, item_id):
        code = 2002
        if cls.objects.filter(name=name).count():
            code = 2017
        elif cls.objects.filter(p_code=p_code).count():
            code = 2017
        if code != 2002:
            return None, code
        try:
            c = cls()
            c.name = name
            c.p_code = p_code
            c.layer = layer_id
            c.group = group_id
            c.item = item_id
            c.save()
            code = code
        except NotUniqueError, e:
            print e
            code = 2018
        return c, code
