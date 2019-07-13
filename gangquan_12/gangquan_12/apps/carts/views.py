from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import GenericAPIView
from django_redis import get_redis_connection
import pickle
import base64
from rest_framework.response import Response
# Create your views here.
from goods.models import SKU
from . import constants
from .serializers import CartsSerializer, CartSKUSerializer, CartDeleteSerializer


class CartView(GenericAPIView):
    """购物车视图"""
    serializer_class = CartsSerializer
    serializer_class = CartDeleteSerializer

    def perform_authentication(self, request):
        """执行具体请求方法前身份认证，由视图自己来进行身份认证"""
        pass

    def post(self, request):
        """保存购物车"""
        # sku_id count  selected
        # 校验

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data['sku_id']
        count = serializer.validated_data['count']
        selected = serializer.validated_data['selected']

        # 判断用户登录状态
        try:
            user = request.user
        except Exception:
            user = None

        # 保存
        if user and user.is_authenticated:
            # 如果用户已登录，保存到redis
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 用户购物车数据 redis hasj哈希
            pl.hincrby('cart_%s' % user.id, sku_id, count)

            # 用户购物车勾选数据 redis  set
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)

            pl.execute()
            return Response(serializer.data)

        else:
            # 如果用户未登录，保存到cookie  response = Response  response.set_cookie
            # 取出cookie中的购物车数据
            cart_str = request.COOKIES.get('cart')

            if cart_str:
                # 解析
                cart_str = cart_str.encode()
                cart_bytes = base64.b64decode(cart_str)
                cart_dict = pickle.loads(cart_bytes)
            else:
                cart_dict = {}

            # 如果商品存在购物车中，累加
            if sku_id in cart_dict:
                cart_dict[sku_id]['count'] += count
                cart_dict[sku_id]['selected'] = selected
            # 如果不在购物车中， 设置
            else:
                cart_dict[sku_id] = {
                    'count':count,
                    'selected':selected
                }
            cart_cookie = base64.b64encode(pickle.dumps(cart_dict)).decode()

            # 设置cookie
            response = Response(serializer.data)
            response.set_cookie('cart', cart_cookie, max_age=constants.CART_COOKIE_EXPIRES)
            # 返回
            return response

    def get(self, request):
        """查询购物车"""
        # 判断用户登录状态
        try:
            user = request.user
        except Exception:
            user = None

        if user and user.is_authenticated:
            # 如果用户已登录，从redis中查询
            redis_conn = get_redis_connection('cart')
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)

            redis_cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

            # 遍历redis_cart, 形成cart_dict
            cart_dict = dict()
            for sku_id, count in redis_cart.items():

                cart_dict[int(sku_id)] = {
                    "count":int(count),
                    'selected':sku_id in redis_cart_selected
                }
        else:
            # 如果用户未查询， 从cookie中查询
            cookie_cart = request.COOKIES.get('cart')

            if cookie_cart:
                # 表示cookie中有购物车数据
                # 解析
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            else:
                # 表示没有数据数据
                cart_dict = dict()

        # 查询数据库

        sku_obj_list = SKU.objects.filter(id__in=cart_dict.keys())

        # 遍历sku_obj_list 向sku对象中添加count和selected属性
        for sku in sku_obj_list:

            sku.count = cart_dict[sku.id]['count']

            sku.selected = cart_dict[sku.id]['selected']
        # 序列化返回
        serializer = CartSKUSerializer(sku_obj_list, many=True)

        return Response(serializer.data)

    def put(self, request):
        """修改购物车"""
        # sku_id  count  selected
        # 校验
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data['sku_id']
        count = serializer.validated_data['count']
        selected = serializer.validated_data['selected']
        # 判断用户状态
        try:
            user = request.user  # 匿名用户为 AnonymoseUser
        except Exception:
            user = None

        if user and user.is_authenticated:
            # 如果已登录修改redis
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()

            # 处理数量 hash
            pl.hset('cart_%s' % user.id, sku_id, count)
            # 处理勾选状态 set
            if selected:
                # 表示勾选
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            else:
                # 表示取消勾选
                pl.srem('cart_selected_%s' % user.id, sku_id)

            pl.execute()
            return Response(serializer.data)

        else:
            # 未登录，修改cookie
            cookie_cart = request.COOKIES.get('cart')

            if cookie_cart:
                # 表示cookie中有购物车数据
                # 解析
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                # 表示cookie中没有购物车数据
                cart_dict = {}

            response = Response(serializer.data)
            if sku_id in cart_dict:
                cart_dict['sku_id'] = {
                    'count':count,
                    'selected':selected
                }
                cart_cookie = base64.b64encode(pickle.dumps(cart_dict)).decode()
                # 设置cookie
                response.set_cookie('cart', cart_cookie, constants.CART_COOKIE_EXPIRES)

                return response

    def delete(self, request):
        """删除购物车"""
        # 获取sku_id
        # 校验
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data['sku_id']
        try:
            user = request.user
        except Exception:
            user = None

        # 判断用户状态
        if user and user.is_authenticated:
            # 已登录删除，redis
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 删除hash
            pl.hdel('cart_%s' % user.id, sku_id)
            # 删除set
            pl.srem('cart_selected_%' % user.id, sku_id)

            pl.execute()

            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # 未登录删除cookie
            cookie_cart = request.COOKIES.get('cart')

            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.decode()))
            else:
                cart_dict = {}

            response = Response(serializer.data)
            if sku_id in cart_dict:
                del cart_dict[sku_id]

            cart_cookie = base64.b64encode(pickle.dumps(cart_dict)).decode()

            response.set_cookie('cart', cart_cookie, max_age=constants.CART_COOKIE_EXPIRES)

            return response








