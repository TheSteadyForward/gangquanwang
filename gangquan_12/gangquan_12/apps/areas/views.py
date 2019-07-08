from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Area
from . import serializers
# Create your views here.


# # GET /areas/
# class AreasView():
#
#     def list(self):
#     # 查询数据库
#     # 序列化返回
#
#     def get(self):
#
# class SubAreasView(RetrieveModelMixin, GenericAPIView):
#     def retrieve(self):

class AreasViewSet(ReadOnlyModelViewSet):

    def get_queryset(self):
        # 通过请求方式指明不同的查询集
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    def get_serializer_class(self):
        # 通过请求方式指明不同的序列化器
        if self.action == 'list':
            return serializers.AreaSerializer
        else:
            return serializers.SubAreaSerializer


# /areas/ {'get':'list'}  # 只返回顶级数据  parent = None
# /areas/ {'get':'retrieve'}  # 返回


