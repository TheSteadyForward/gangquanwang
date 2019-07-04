from rest_framework import serializers
from django_redis import get_redis_connection


class ImageCodeCheckSerializer(serializers.Serializer):
    """
    图片验证码序列化器
    """

    image_code_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4, min_length=4)

    def validate(self, attrs):

        # 获取image_code_id 进行后期redis数据库查询
        image_code_id = attrs['image_code_id']
        # 获取text 进行与redis数据库中文本验证码进行校验
        text = attrs['text']

        # 查询真实图片验证码
        # 生成redis 对象方便后面尽心查询
        redis_conn = get_redis_connection('verify_codes')
        # 进行查询 文本验证码
        real_image_code_text = redis_conn.get('img_%s' % image_code_id)

        # 如果文本验证码为空，那么就是id 错误 或者 已经失效
        if not real_image_code_text:
            raise serializers.ValidationError('图片验证码无效')

        # 删除redis图片验证码
        redis_conn.delete('img_%s' % image_code_id)

        # 校验输入验证码是否一致
        real_image_code_text = real_image_code_text.decode()
        if real_image_code_text.lower() != text.lower():
            raise serializers.ValidationError('验证码输入不正确')

        # 判断是否在60秒以内
        # get_serializer 方法创建序列化器对象的时候，会补充context属性
        # context 属性中三个值 request format view(类视图对象)
        # self.context('view')

        # django的类视图对象中， kwargs属性保存了路径提取出来的参数
        # 通过get_serializer中context中 view(类视图对象)属性中kwargs中取出来mobile
        mobile = self.context['view'].kwargs['mobile']
        # 通过mobile进行在数据库中是否有对应的数值
        send_flag = redis_conn.get('send_flag_%s' % mobile)

        # 如果有对应值，说明60秒内已经请求过一次了，说明请求次数国语频繁
        if send_flag:
            raise serializers.ValidationError('请求过于频繁')

        return attrs
