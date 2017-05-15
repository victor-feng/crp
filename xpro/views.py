# _*_coding:utf-8_*_
# from django.shortcuts import render
#
# Create your views here.
#
import json
import logging
from __builtin__ import len

from django.http import JsonResponse
from xpro.models import RepoItem, RepoItemString, RepoItemInt, RepoItemDatetime
from rest_framework.views import APIView

logger = logging.getLogger('django.xpro')
logger.setLevel(logging.DEBUG)


_SUCCESSFUL_ID = {'code': 0}


class RepoItemView(APIView):
    def _property_string_insert(self, property, item):
        name = property.get('name')
        default_value = property.get('value')
        item_string = RepoItemString(name=name, default_value=default_value)
        try:
            item.repoitem_string.append(item_string)
            item.save()
        except Exception as e:
            print e
            return 2003
        code = 2002
        return code

    def _property_int_insert(self, property, item):
        name = property.get('name')
        default_value = property.get('value')
        unit = property.get('unit')
        item_int = RepoItemInt(name=name, unit=unit, default_value=default_value)
        item.repoitem_int.append(item_int)
        item.save()
        code = 2002
        return code

    def _property_datetime_insert(self, property, item):
        name = property.get('name')
        default_value = property.get('value')
        item_dt = RepoItemDatetime(name=name, default_value=default_value)
        item.repoitem_datetime.append(item_dt)
        item.save()
        code = 2002
        return code

    def post(self, request, format=None):
        data = json.loads(request.body)
        name = data.get('name')
        p_code = data.get('id')
        layer_id = data.get('layer_id')
        group_id = data.get('group_id')
        item_id = data.get('item_id')

        propertylist = data.get('property_list')

        repo_item, code = RepoItem.created_repoitem(name, p_code, layer_id, group_id, item_id)
        if code != 2002:
            res = {
                "code": code,
                "result": {
                    "res": name,
                    "msg": '2000'  # RESPONSE_CONTENT[str(code)]
                }
            }
            return JsonResponse(res)

        for property in propertylist:
            type = property.get('type')
            if type == 'string':
                code = self._property_string_insert(property, repo_item)
            elif type == 'int':
                code = self._property_int_insert(property, repo_item)
            elif type == 'datetime':
                code = self._property_datetime_insert(property, repo_item)

        res = {
            "code": code,
            "result": {
                "res": name,
                "msg": '2000'  # RESPONSE_CONTENT[str(code)]
            }
        }
        return JsonResponse(res)


def response_data(code, res):
    res = {
            'code': code,
            'result': {
                'res': res,
                'msg': '2000'  # RESPONSE_CONTENT[str(code)]
                }
            }
    return res


class RepoItemDetail(APIView):
    def get(self, request, item_id):
        res_list = []
        code = 2002
        try:
            items = RepoItem.objects.filter(item=item_id)
            if len(items):
                for i in items:
                    tmp_list = []
                    res = {}
                    if len(i.repoitem_string) > 0:
                        tmp_list.extend(i.repoitem_string)
                    if len(i.repoitem_int) > 0:
                        tmp_list.extend(i.repoitem_int)
                    if len(i.repoitem_datetime) > 0:
                        tmp_list.extend(i.repoitem_datetime)
                    for string in tmp_list:
                        res[string.name] = string.default_value
                    res_list.append(res)
        except Exception as e:
            code = 500

        ret = response_data(code, res_list)
        return JsonResponse(ret)
