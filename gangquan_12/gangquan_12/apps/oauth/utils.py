from django.conf import settings
import urllib.parse
from urllib.request import urlopen
import logging
import re
import json
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSerializer, BadData

from .exceptions import OAuthQQAPIerror
from . import constants

logger = logging.getLogger('django')


class OAuthQQ(object):
    """
    QQ认证辅助工具
    """
    def __init__(self, cilent_id=None, redirect_uri=None, state=None, client_secret=None):
        self.client_id = cilent_id if cilent_id else settings.QQ_CLIENT_ID
        self.redirect_uri = redirect_uri if redirect_uri else settings.QQ_REDIRECT_URI
        # self.state = state if cilent_id else settings.QQ_client_id
        self.state = state or settings.QQ_STATE
        self.client_secret = client_secret or settings.QQ_CLIENT_SECRET

    def get_login_url(self):
        url = 'https://graph.qq.com/oauth2.0/authorize?'

        params = {
            'response_type':'code',
            'client_id':self.client_id,
            'redirect_uri':self.redirect_uri,
            'state':self.state
        }

        url += urllib.parse.urlencode(params)

        return url

    def get_access_token(self, code):
        """获取acces_token"""
        url = 'https://graph.qq.com/oauth2.0/token?'

        params = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }

        url += urllib.parse.urlencode(params)

        try:
            # 发送请求
            resp = urlopen(url)
            # 读取响应数据
            resp_data = resp.read().decode()
            # 解析access_token
            resp_dict = urllib.parse.parse_qs(resp_data)
        except Exception as e:
            logger.error('获取access_token异常%s' % e)
            raise OAuthQQAPIerror
        else:
            access_token = resp_dict.get('access_token')
            print(access_token)

        return access_token[0]

    def get_openid(self, access_toke):
        """获取openid"""
        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_toke

        try:
            response = urlopen(url)
            response_data = response.read().decode()

            # 返回的数据 callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} )\n;
            resp_dict = response_data[10:-4]
            # resp_dict = re.search(r'\{\w+\}')
            resp_dict = json.loads(resp_dict)
        except Exception as e:
            raise OAuthQQAPIerror

        else:
            openid = resp_dict.get('openid')

        return openid

    def generate_bind_user_access_token(self, openid):

        serializer = TJWSerializer(settings.SECRET_KEY, expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
        data = {'openid':openid}
        token = serializer.dumps(data)
        return token.decode()

    @staticmethod
    def check_save_user_token(token):
        """
        检验保存用户数据的token
        :param token:
        :return:
        """
        serializer = TJWSerializer(settings.SECRET_KEY, expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            return data.get('openid')




