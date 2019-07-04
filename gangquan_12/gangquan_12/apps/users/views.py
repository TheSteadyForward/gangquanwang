from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import User
# Create your views here.


class UsernameCountView(APIView):

    def get(self, request, username):
        """获取用户数量"""
        count = User.objects.get(username=username).count()

        return Response({
            'username':username,
            'count':count
        })


class MobileCountView(APIView):
    """获取手机号数量"""
    def get(self, request, mobile):
        count = User.objects.get(mobile=mobile).count()

        return Response({
            'mobile':mobile,
            'count':count
        })