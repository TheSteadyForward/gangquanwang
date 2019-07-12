#!/usr/bin/env python

"""
功能：手动生成所有SKU的静态文件detail html文件
使用方法：
    ./regenerate_index_html.py
"""
import sys
sys.path.insert(0, '../')
sys.path.insert(0, '../gangquan_12/apps')

import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'gangquan_12.settings.dev'


# 让django进行初始haunted设置
import django
django.setup()

from contents.crons import generate_static_index_html


if __name__ == '__main__':
    generate_static_index_html()