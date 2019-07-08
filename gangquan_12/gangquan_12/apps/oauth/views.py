from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from rest_framework.views import APIView
import logging
from rest_framework.generics import CreateAPIView

from oauth.models import OAuthQQUser
from oauth.serializers import OAuthQQUserSerializer
from .utils import OAuthQQ
from .exceptions import OAuthQQAPIerror
# Create your views here.

logger = logging.getLogger('django')


# url(r'qq/authorization/$', views.QQAuthURLView.as_view())
class QQAuthURLView(APIView):
    """
    获取QQ登录url
    """
    def get(self, request):
        # 获取next参数
        next = request.query_params.get('next')
        # 拼接QQ登录网址
        oauth_qq = OAuthQQ(state=next)
        login_url = oauth_qq.get_login_url()
        #　返回

        return Response({'login_url':login_url})


class QQAuthUserView(CreateAPIView):
    """
    QQ登录的用户
    """
    serializer_class = OAuthQQUserSerializer

    def get(self, request):
        # 获取code
        code = request.query_params.get('code')
        # print(code)
        # 凭借code 获取access_token
        if not code:
            return Response({'message':'缺少code'}, status=status.HTTP_400_BAD_REQUEST)
        # 凭借access_token 获取 openid
        oauth_qq = OAuthQQ()
        try:
            access_token = oauth_qq.get_access_token(code)
            # print(access_token)
            openid = oauth_qq.get_openid(access_token)
            # print(openid)
        except OAuthQQAPIerror as e:
            logger.error('获取QQ接口异常 %s' % e)
            return Response({'message':'获取QQ接口异常'}, status=status.HTTP_400_BAD_REQUEST)

        # 根据openid查找数据库  OAuthQQUser  判断是否存在
        try:
            oauth_qq_user = OAuthQQUser.objects.get(openid=openid)

        except OAuthQQUser.DoesNotExist:
            access_token = oauth_qq.generate_bind_user_access_token(openid)
            return Response({'access_token':access_token})
        else:
            #　如果存在，表示用户已经绑定身份，　签发　ＪＷＴ ｔｏｋｅｎ
            # 签发jwt token
            user = oauth_qq_user.user
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            return Response({
                'token': token,
                'user_id': user.id,
                'username': user.username
            })

"""
    def post(self, request):
        
        # 保存QQ登录用户
        # :param request:
        # :return:
        
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 生成已登录的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        return Response({
            'token':token,
            'user_id':user.id,
            'username':user.username
        })
"""







