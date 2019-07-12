from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework.generics import UpdateAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import GenericAPIView
from django_redis import get_redis_connection

from .serializers import CreateUserSerializer, UserDetailSerializer, EmailSerializer, UserAddressSerializer, \
    AddressTitleSerializer, AddUserBrowsingHistorySerializer, SKUSerializer
from .models import User
from . import constants
from goods.models import SKU
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


# 新增 POST /addresses/
# 修改 PUT  /assresses/<pk>
# 查询 GET  /addresses/
# 删除 DELETE /addresses/<pk>

# 设置默认地址  PUT /addresses/<pk>/atatu  # 设置默认地址，就是改变地址的状态，所以参数为status
# 设置地址标题  PUT /addresses/<pk>/title
class AddressViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = UserAddressSerializer

    def get_queryset(self):
        # 改写get_queryset 不要查询已经被删除的地址数据
        return self.request.user.addresses.filter(is_deleted=False)

    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user

        return Response({
            'user_id':user.id,
            'default_address_id':user.default_address_id,
            'limit':constants.USER_ADDRESS_COUNT_LIMIT,
            'addresses':serializer.data
        })

    def create(self, request, *args, **kwargs):
        """
        用户爆保存地址数据
        :param request:请求对象
        """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNT_LIMIT:
            return Response({'message':'保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """
        设置默认地址
        :param request:请求对象
        :param pk: 需要修改的pk
        :return:
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()

        return Response({'message':'OK'}, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None, address_id=None):
        """
        修改标题
        :param request:
        :param pk:
        :param address_id:
        :return:
        """
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class UserBrowsingHistorView(mixins.CreateModelMixin, GenericAPIView):
    """
    用户历史记录
    """
    serializer_class = AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        保存
        :param request:
        :return:
        """
        return self.create(request)

    def get(self, request):
        """
        获取
        """
        user_id = request.user.id

        redis_conn = get_redis_connection('history')
        history = redis_conn.lrange('history_%s' % user_id, 0, constants.USER_BROWSING_HISTORY_COUNT_LIMIT)
        skus = []
        # 为保持查询出的顺序呢与用户的浏览历史保存顺序一致
        for sku_id in history:
            sku = SKU.objects.get(id=sku_id)
            skus.append(sku)

        s = SKUSerializer(skus, many=True)
        return Response(s.data)












