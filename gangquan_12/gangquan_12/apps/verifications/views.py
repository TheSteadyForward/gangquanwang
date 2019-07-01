from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from gangquan_12.libs.captcha.captcha import captcha
from django_redis import get_redis_connection

from . import constants
# Create your views here.


class ImageCodeView(APIView):  # 继承View  视图函数  接收请求：HttpRequest  响应请求：HttpResponse
    """图片验证码视图"""

    def get(self, request, image_code_id):


        # 生成验证码图片
        text, image = captcha.generate_captcha()

        # 保存真实值
        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex('img_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES , text)

        # 返回图片
        return HttpResponse(image, content_type='image/jpg')





