import re

from rest_framework import serializers
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from .models import User


class CreateUserSerializer(serializers.ModelSerializer):
    """创建用户序列化器"""
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    token = serializers.CharField(label='jwt token', read_only=True)


    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow', 'token']
        extra_kwargs = {
            'username':{
                'min_length':5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的密码',
                    'max_length': '仅允许5-20个字符的密码'
                }
            },
            'password':{
                'write_only':True,
                'min_length':8,
                'max_length':20,
                'error_messages':{
                    'min_length':'仅允许8-20个字符的密码',
                    'max_length':'仅允许8-20个字符的密码'
                }
            }
        }

    def validate_mobile(self, value):
        """验证手机号"""
        if not re.match(r'1[3-9]\d{9}', value):
            raise serializers.ValidationError('手机格式错误')
        return value

    def validate_allow(self, value):
        """验证用户协议是否同意"""
        if value != 'true':
            raise serializers.ValidationError('用户协议未同意')
        return value

    def validate(self, attrs):
        """判断多个字段进行验证"""
        if attrs['password2'] != attrs['password']:
            """密码校验"""
            raise serializers.ValidationError('密码输入不一致')

        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % attrs['mobile'])
        if not real_sms_code:
            raise serializers.ValidationError('短信验证码已经失效')
        if real_sms_code.decode() != attrs['sms_code']:
            """短信验证码校验"""
            raise serializers.ValidationError('短信验证码输入错误')

        return attrs

    def create(self, validated_data):
        """重写保存方法，增加密码加密"""
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        # user = User.objects.create(**validated_data)
        user = super().create(validated_data)

        user.set_password(validated_data['password'])
        user.save()

        # 签发jwt token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        user.token = token

        return user











