import random
import logging
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from gangquan_12.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from rest_framework.generics import GenericAPIView
from rest_framework.views import status

from . import constants
from .serializers import ImageCodeCheckSerializer
from gangquan_12.utils.yuntongxun.sms import CCP
from celery_tasks.sms.tasks import send_sms_code
# Create your views here.

loger = logging.getLogger('django')


class ImageCodeView(APIView):  # 继承View  视图函数  接收请求：HttpRequest  响应请求：HttpResponse
    """图片验证码视图"""

    def get(self, request, image_code_id):


        # 生成验证码图片
        text, image = captcha.generate_captcha()

        # 保存真实值
        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex('img_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES , text)
        print(text)
        # 返回图片
        return HttpResponse(image, content_type='image/jpg')


class SMSCodeView(GenericAPIView):
    """
    短信验证码
    传入参数
        mobile  image_code_id, text
    """
    serializer_class = ImageCodeCheckSerializer
    def get(self, request, mobile):
        # 校验参数  由序列化器完成
        print(request.query_params)
        serialzier = self.get_serializer(data=request.query_params)
        serialzier.is_valid(raise_exception=True)

        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)

        # 保存短信验证码
        redis_conn = get_redis_connection('verify_codes')
        # redis_conn.setex('sms_%s' % sms_code, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # redis 管道
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % sms_code, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, constants.SMS_CODE_TEMP_ID)

        # 通知pipeline执行命令
        pl.execute()

        print(sms_code)

        # try:
        #     # 发送短信
        #     ccp = CCP()
        #     expires = constants.SMS_CODE_REDIS_EXPIRES // 60
        #     result = ccp.send_template_sms(mobile, [sms_code, expires], constants.SMS_CODE_TEMP_ID)
        # except Exception as e:
        #     loger.error('发送短信验证码(异常) mobile:%s, message: %s' % (mobile, e))
        #     return Response({'message':'发送信息异常'}, status=status.HTTP_507_INSUFFICIENT_STORAGE)
        # if result == 0:
        #     loger.info('发送短信验证码(正常) mobile:%s' % mobile)
        #     return Response({'message':'发送信息成功'}, status=status.HTTP_200_OK)
        # else:
        #     loger.warning('发送短信验证码(失败) mobile:%s' % mobile)
        #     return Response({'message':'发送信息失败'}, status=status.HTTP_507_INSUFFICIENT_STORAGE)

        # 使用celery发送
        expires = constants.SMS_CODE_REDIS_EXPIRES // 60
        send_sms_code.delay(mobile, sms_code, expires, constants.SMS_CODE_TEMP_ID)

        return Response({'message':'ok'})



