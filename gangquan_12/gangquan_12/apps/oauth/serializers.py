from rest_framework import serializers
from django_redis import get_redis_connection

from users.models import User
from .utils import OAuthQQ
from oauth.models import OAuthQQUser


class OAuthQQUserSerializer(serializers.ModelSerializer):
    """
    QQ登录创建用户序列化器
    """
    # password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    access_token = serializers.CharField(label='操作凭证', write_only=True)
    token = serializers.CharField(read_only=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')

    class Meta:
        model = User
        fields = ('mobile', 'password', 'sms_code', 'access_token', 'id', 'username', 'token')
        extra_kwargs = {
            'username':{
                'read_only':True
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

    def validate(self, attrs):
        # 检验access_toke
        access_token = attrs['access_token']
        # print(access_token)
        openid = OAuthQQ.check_save_user_token(access_token)
        if not openid:
            raise serializers.ValidationError('无效的access_token')

        attrs['openid'] = openid

        # 检验短信验证码
        mobile = attrs['mobile']
        sms_code = attrs['sms_code']
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code.decode() != sms_code:
            raise serializers.ValidationError('短信验证码错误')

        # 如果用户存在
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            pass
        else:
            password = attrs['password']

            if not user.check_password(password):
                raise serializers.ValidationError('密码输入错误')

            attrs['user'] = user

        return attrs

    def create(self, validated_data):
        user = validated_data.get('user')
        if not user:
            # 用户不存在
            user = User.objects.create_user(
                username=validated_data['mobile'],
                password=validated_data['password'],
                mobile=validated_data['mobile'],
            )

        OAuthQQUser.objects.create(
            openid=validated_data['openid'],
            user=user
        )

        return user

