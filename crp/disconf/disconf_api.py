# -*- coding: utf-8 -*-

import requests
import json
import os
import shutil

session = requests.Session()


class ServerError(Exception):
    pass


def exchange_disconf_name(name):
    try:
        disconf_with_uuid = name
        disconf_no_uuid = ''.join(disconf_with_uuid.split(',')[:-1])
        if os.path.isfile(disconf_no_uuid):
            os.remove(disconf_no_uuid)
        shutil.copy2(disconf_with_uuid,disconf_no_uuid)
    except Exception as e:
        raise ServerError(e.message)
    return disconf_no_uuid


class DisconfServerApi(object):
    def __init__(self,disconf_server_info):
        self.disconf_server_name = disconf_server_info.get('disconf_server_name')
        #self.disconf_url = 'http://172.28.18.48:8081'
        #self.disconf_user_info = {'name': 'admin', 'password': 'admin', 'remember': '0'}
        self.disconf_url = disconf_server_info.get('disconf_server_url')
        self.disconf_user_info = {'name':disconf_server_info.get('disconf_server_user'),'password':disconf_server_info.get('disconf_server_password'),'remember':'0'}
        self.SIGNIN = self.disconf_url + '/api/account/signin'
        self.SESSION = self.disconf_url + '/api/account/session'
        self.APP = self.disconf_url + '/api/app'
        self.FILETEXT = self.disconf_url + '/api/web/config/filetext'
        self.FILE = self.disconf_url + '/api/web/config/file'
        self.APP_LIST = self.disconf_url + '/api/app/list'
        self.ENV_LIST = self.disconf_url + '/api/env/list'
        self.VERSION_LIST = self.disconf_url + '/api/web/config/versionlist'
        self.CONFIG_LIST = self.disconf_url + '/api/web/config/list'
        self.CONFIG_SHOW = self.disconf_url + '/api/web/config'
        self.CONFIG_DEL = self.disconf_url + '/api/web/config'


    def disconf_signin(self):
        user_info = self.disconf_user_info
        SIGNIN = self.SIGNIN
        try:
            rep = requests.post(SIGNIN, data=user_info)
            ret_json = json.loads(rep.text)
            result = ret_json.get('success')

            if result != 'true':
                message = 'ERROR:{result}'.format(result=ret_json)
                raise ServerError(message)

        except Exception as e:
            raise ServerError(e.message)
        return ret_json


    def disconf_session(self):
        user_info = self.disconf_user_info
        SIGNIN = self.SIGNIN
        try:
            res = session.post(SIGNIN, data=user_info)
            ret_json = json.loads(res.text)
            result = ret_json.get('success')

            if result != 'true':
                message = 'ERROR:{result}'.format(result=ret_json)
                raise ServerError(message)

        except Exception as e:
            raise ServerError(e.message)
        return ret_json

    def disconf_app(self, app_name, desc):
        app_info = {'app': app_name, 'desc': desc, 'emails': ''}
        APP = self.APP
        try:
            self.disconf_session()
            rep = session.post(APP, data=app_info)
            ret_json = json.loads(rep.text)
            result = ret_json.get('success')

            if result != 'true':
                message = 'ERROR:{result}'.format(result=ret_json)
                raise ServerError(message)

        except Exception as e:
            raise ServerError(e.message)
        return ret_json


    def disconf_file(self,appId, envId, version, myfilerar):
        try:
            file_content = {
                        'appId': (None,str(appId)),
                        'envId': (None,str(envId)),
                        'version': (None,str(version)),
                        'myfilerar': open(myfilerar,'rb')
                        }

            self.disconf_session()
            FILE = self.FILE
            rep = session.post(FILE, files=file_content)
            ret_json = json.loads(rep.text)
            result = ret_json.get('success')

            if result != 'true':
                message = 'ERROR:{result}'.format(result=ret_json)
                raise ServerError(message)

        except Exception as e:
            raise ServerError(e.message)
        return ret_json


    def disconf_filetext(self, appId, envId, version, fileContent, fileName):
        try:
            filetext = {
                        'appId': appId,
                        'envId': envId,
                        'version': version,
                        'fileContent': fileContent,
                        'fileName': fileName
                        }
            self.disconf_session()
            FILETEXT = self.FILETEXT
            rep = session.post(FILETEXT, data=filetext)
            ret_json = json.loads(rep.text)
            result = ret_json.get('success')

            if result != 'true':
                message = 'ERROR:{result}'.format(result=ret_json)
                raise ServerError(message)

        except Exception as e:
            raise ServerError(e.message)
        return ret_json


    def disconf_filetext_update(self, config_id, filecontent):
        try:
            url = '{filetext}/{config_id}'.format(filetext=self.FILETEXT, config_id=config_id)
            filetext = {
                        'fileContent': filecontent
                        }
            self.disconf_session()
            rep = session.put(url, data=filetext)
            ret_json = json.loads(rep.text)
            result = ret_json.get('success')

            if result != 'true':
                message = 'ERROR:{result}'.format(result=ret_json)
                raise ServerError(message)

        except Exception as e:
            raise ServerError(e.message)
        return ret_json


    def disconf_filetext_delete(self, config_id):
        try:
            url = '{config_del}/{config_id}'.format(config_del=self.CONFIG_DEL, config_id=config_id)
            self.disconf_session()
            rep = session.delete(url)
            ret_json = json.loads(rep.text)
            result = ret_json.get('success')

            if result != 'true':
                message = 'ERROR:{result}'.format(result=ret_json)
                raise ServerError(message)

        except Exception as e:
            raise ServerError(e.message)
        return ret_json


    def disconf_app_list(self):
        try:
            self.disconf_session()
            APP_LIST = self.APP_LIST
            rep = session.get(APP_LIST)
            ret_json = json.loads(rep.text)
            result = ret_json.get('success')
            app_list = ret_json.get('page').get('result')

            if result != 'true':
                message = 'ERROR:{result}'.format(result=ret_json)
                raise ServerError(message)

        except Exception as e:
            raise ServerError(e.message)
        return app_list


    def disconf_app_id(self, app_name):
        try:
            app_id = None
            self.disconf_session()
            app_list = self.disconf_app_list()
            for name in app_list:
                # name.get('name') is unicode
                if name.get('name') == app_name:
                    # app_id is instance of int
                    app_id = name.get('id')
                    break
        except ServerError as e:
            raise ServerError(e.message)
        return app_id


    def disconf_env_list(self):
        try:
            self.disconf_session()
            ENV_LIST = self.ENV_LIST
            rep = session.get(ENV_LIST)
            ret_json = json.loads(rep.text)
            result = ret_json.get('success')
            env_list = ret_json.get('page').get('result')
            if result != 'true':
                message = 'ERROR:{result}'.format(result=ret_json)
                raise ServerError(message)

        except Exception as e:
            raise ServerError(e.message)
        return env_list


    def disconf_env_id(self, env_name):
        try:
            env_id = None
            self.disconf_session()
            env_list = self.disconf_env_list()
            if env_list:
                for env in env_list:
                    if env.get('name') == env_name:
                        env_id = env.get('id')
                        break
        except Exception as e:
            raise ServerError(e.message)
        return env_id


    def disconf_env_name(self, env_id):
        try:
            env_name = None
            if (env_id is None) or (len(env_id.strip()) == 0):
                return ""

            self.disconf_session()
            env_list = self.disconf_env_list()
            if env_list:
                for env in env_list:
                    if env.get('id') == int(env_id):
                        env_name = env.get('name')
                        break
        except Exception as e:
            raise ServerError(e.message)
        return env_name


    def disconf_version_list(self, app_id):
        try:
            url = '{version_list}?appId={app_id}'.format(version_list=self.VERSION_LIST, app_id=app_id)
            self.disconf_session()
            rep = session.get(url)
            ret_json = json.loads(rep.text)
            result = ret_json.get('success')

            if result == 'true':
                result_list = ret_json.get('page').get('result')
                if result_list:
                    version_id = ret_json.get('page').get('result')[0]
                else:
                    version_id = None
            else:
                version_id = None

        except Exception as e:
            raise ServerError(e.message)
        return version_id


    def disconf_config_list(self, app_id, env_id, version): ##config可以为空[]
        try:
            url = '{config_list}?appId={app_id}&envId={env_id}&version={version}&'.format(
                    config_list=self.CONFIG_LIST, app_id=app_id, env_id=env_id, version=version)
            self.disconf_session()
            rep = session.get(url)
            ret_json = json.loads(rep.text)
            result = ret_json.get('success')

            if result == 'true':
                config_list = ret_json.get('page').get('result')
            else:
                config_list = []

        except Exception as e:
            raise ServerError(e.message)
        return config_list

    def disconf_config_id_list(self, app_id, env_id, version):
        try:
            config_list = self.disconf_config_list(app_id, env_id, version)
            config_id_list = []
            if config_list:
                for config in config_list:
                    config_id_list.append(config.get('configId'))
        except Exception as e:
            raise ServerError(e.message)
        return config_id_list


    def disconf_config_id(self, app_id, env_id, config_name, version):
        try:
            config_id = None
            config_list = self.disconf_config_list(app_id, env_id, version)
            if config_list:
                for config in config_list:
                    if config.get('key') == config_name:
                            config_id = config.get('configId')
                            break
        except Exception as e:
            raise ServerError(e.message)
        return config_id


    def disconf_config_name_list(self, app_id, env_id, version):
        try:
            config_list = self.disconf_config_list(app_id, env_id, version)
            config_name_list = []
            if config_list:
                for config in config_list:
                    config_name_list.append(config.get('key'))
        except Exception as e:
            raise ServerError(e.message)
        return config_name_list


    def disconf_config_show(self, config_id):
        try:
            url = '{config_show}/{config_id}'.format(config_show=self.CONFIG_SHOW, config_id=config_id)
            self.disconf_session()
            rep = session.get(url)
            ret_json = json.loads(rep.text)
            result = ret_json.get('success')
            if result == 'true':
                config = ret_json.get('result')
            else:
                config = None
        except Exception as e:
            raise ServerError(e.message)
        return config


    def disconf_add_app_config_api_content(self, app_name, filename, filecontent, version, env_id):
        try:
            app_id = self.disconf_app_id(app_name)
            if app_id is None:
                app_desc = '{res_name} config generated.'.format(res_name=app_name)
                self.disconf_app(app_name, app_desc)
                app_id = self.disconf_app_id(app_name)

            config_id = self.disconf_config_id(app_id=app_id, env_id=env_id, config_name=filename,version=version)
            if config_id is None:
                ret = self.disconf_filetext(app_id, env_id, version, fileContent=filecontent, fileName=filename)
            else:
                self.disconf_filetext_delete(config_id)
                ret = self.disconf_filetext(app_id, env_id, version, fileContent=filecontent, fileName=filename)
            result = 'success'
            message = 'instance_name:{ins_name},filename:{filename} success'.format(ins_name=app_name,filename=filename)
        except Exception as e:
            result = 'fail'
            message = e.message
        return result,message


    def disconf_add_app_config_api_file(self, app_name, myfilerar, version, env_id):
        try:
            app_id = self.disconf_app_id(app_name)
            if app_id is None:
                app_desc = '{res_name} config generated.'.format(res_name=app_name)
                self.disconf_app(app_name, app_desc)
                app_id = self.disconf_app_id(app_name)
            filename = myfilerar.split('/')[-1]
            config_id = self.disconf_config_id(app_id=app_id, env_id=env_id, config_name=filename,version=version)
            if config_id is None:
                ret = self.disconf_file(app_id, env_id, version, myfilerar)
            else:
                self.disconf_filetext_delete(config_id)
                ret = self.disconf_file(app_id, env_id, version, myfilerar)

            result = 'success'
            message = 'instance_name:{ins_name},filename:{filename} success'.format(ins_name=app_name,filename=filename)
        except Exception as e:
            result = 'fail'
            message = e.message
        return result,message

    def disconf_get_app_config_api(self, app_name, env_id):
        try:
            app_id = self.disconf_app_id(app_name=app_name)
            version_id = self.disconf_version_list(app_id=app_id)
            config_id_list = self.disconf_config_id_list(app_id=app_id, env_id=env_id, version=version_id)

            configurations = []
            for config_id in config_id_list:
                config = self.disconf_config_show(config_id)
                config_value = {}
                if config is not None:
                    config_value['filename'] = config.get('key')
                    config_value['filecontent'] = config.get('value')
                    config_value['config_id'] = config.get('configId')
                    configurations.append(config_value)
        except Exception as e:
            raise ServerError(e.message)
        return configurations


if __name__ == '__main__':
    version = "1_0_0"
    app_name = 'wzy_test_0001'
    env_id = '1'
    filename = 'test2'
    filecontent = 'dsfsdfsfs-new-add>>>>>>>>>>>>>>>>>'
    myfilerar = '/root/test.py'
    name = '/opt/test111,147ab190-87af-11e7-af82-fa163e9474c9'
    server_info = {'disconf_server_name':'172.28.11.111',
                   'disconf_server_url':'http://172.28.11.111:8081',
                   'disconf_server_user':'admin',
                   'disconf_server_password':'admin',
                   }
    disconf_api = DisconfServerApi(server_info)
    print disconf_api.disconf_server_name
    print disconf_api.disconf_url
    print disconf_api.disconf_user_info
    print disconf_api.disconf_app_list()
    print disconf_api.disconf_env_list()
    #print disconf_api.disconf_app(app_name='final71',desc='sfsdf')
    #print disconf_api.disconf_get_app_config_api(app_name='final71',env_id='1')
    #print disconf_api.disconf_env_name(env_id='2')
    #print exchange_disconf_name(name)
    #print disconf_app_list()
    #print disconf_env_list()
    #print disconf_version_list(app_id=70)
    #print disconf_env_id('rd')
    #print disconf_env_name(env_id="")
    #print disconf_api.disconf_add_app_config_api_content(app_name, filename, filecontent, version='0_0_0_1', env_id='1')
    #print disconf_api.disconf_add_app_config_api_file(app_name, myfilerar, version='0_0_0_1', env_id='1')
    #print disconf_get_app_config_api(app_name, env_id)
