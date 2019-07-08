from celery import Celery
import os

if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'gangquan_12.settings.dev'

# 创建celery应用
celery_app = Celery('gangquan_12')

# 导入celery配置
celery_app.config_from_object('celery_tasks.config')

# 导入任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])



