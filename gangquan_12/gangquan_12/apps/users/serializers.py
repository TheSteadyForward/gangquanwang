import re
from rest_framework import serializers
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings
from django_redis import get_redis_connection

from .models import User, Address
from celery_tasks.email.tasks import send_active_email
from goods.models import SKU
from .constants import USER_BROWSING_HISTORY_COUNT_LIMIT


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


class UserDetailSerializer(serializers.ModelSerializer):
    """
    用户详细信息序列化器
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'mobile', 'email', 'email_active']


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']

    def update(self, instance, validated_data):
        """

        :param instance: 视图传送过来的user对象
        :param validated_data:
        :return:
        """
        email = validated_data['email']

        instance.email = email
        instance.save()

        # 生成激活链接
        url = instance.generate_verify_email_url()

        # 发送邮件
        send_active_email.delay(email, url)

        return instance


class UserAddressSerializer(serializers.ModelSerializer):
    """
    用户地址序列化器
    """
    """
    省份名字
    市份名字
    地区名字
    省份ID
    市份ID
    地区ID
    """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省份ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def validate_mobile(self, value):
        """验证手机号"""
        if not re.match(r'^1[3-9]\d{9}', value):
            raise serializers.ValidationError('手机号格式错误')

        return value

    def create(self, validated_data):
        """
        保存
        """
        validated_data['user'] = self.context['request'].user

        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址修改
    """
    class Meta:
        model = Address
        fields = ['title']


class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """
    添加用户浏览器历史序列化器
    """
    sku_id = serializers.IntegerField(label="商品SKU编号", min_value=1)
    def validate_suk_id(self, value):
        """
        校验sku_id是否存在
        """
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('该商品不存在')

        return value

    def create(self, validated_data):
        """
        保存
        :param validated_data:
        :return:
        """
        user_id = self.context['request'].user.id
        sku_id = validated_data['sku_id']

        redis_conn = get_redis_connection('history')

        # 创建redis管道
        pl = redis_conn.pipeline

        # 移除已经存在的本商品浏览记录
        pl.lrem('history_%s' % user_id, 0, sku_id)
        # 添加新的记录
        pl.lpush('history_%s' % user_id, sku_id)
        # 只保存最多5条记录
        pl.ltrin('history_%s' % user_id, 0, constants.USER_BROWSING_HISTORY_COUNT_LIMIT-1)

        pl.execute()

        return validated_data


class SKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')












