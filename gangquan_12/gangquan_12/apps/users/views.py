from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
# from rest_framework.generics import mixins
from rest_framework.generics import CreateAPIView
from .serializers import CreateUserSerializer


from .models import User
# Create your views here.


class UserVIew(CreateAPIView):
    """
    用户注册
    传入参数
        username, password, password2, sms_code, mobile, allow
    """
    serializer_class = CreateUserSerializer


class UsernameCountView(APIView):

    def get(self, request, username):
        """获取用户数量"""
        count = User.objects.filter(username=username).count()

        return Response({
            'username':username,
            'count':count
        })


class MobileCountView(APIView):
    """获取手机号数量"""
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()

        return Response({
            'mobile':mobile,
            'count':count
        })




