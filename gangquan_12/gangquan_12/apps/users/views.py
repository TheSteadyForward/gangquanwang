from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework.generics import UpdateAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from .serializers import CreateUserSerializer, UserDetailSerializer, EmailSerializer
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


class UserDetailView(RetrieveAPIView):
    """
    用户基本信息
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # 返回当前请求用户
        # 在类视图对象中，可以通过
        return self.request.user


# PUT /email/
class EmailView(UpdateAPIView):
    """保存email"""
    serializer_class = EmailSerializer

    def get_object(self):
        return self.request.user

    # def put(self):
    #     # 获取email
    #     # 校验email
    #     # 查询user
    #     # 更新数据
    #     # 序列化返回


class VerifyEmail(APIView):
    """
    邮箱验证
    """
    def get(self, request):

        token = request.query_params.get('token')

        if not token:
            return Response({'message':'没有token值'}, status=status)

        user = User.check_verify_email_token(token)

        if user is None:
            return Response({'message':'链接信息无效'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.email_active = True
            user.save()
            return Response({'message':'ok'})

