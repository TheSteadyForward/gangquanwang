from .utils.yuntongxun.sms import CCP
import logging
from celery_tasks.main import celery_app

logger = logging.getLogger('django')


@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code, expires, temp_id):
    """发送短信验证码"""

    try:
        # 发送短信
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [sms_code, expires], temp_id)
    except Exception as e:
        logger.error('发送短信验证码(异常) mobile:%s, message: %s' % (mobile, e))

    if result == 0:
        logger.info('发送短信验证码(正常) mobile:%s' % mobile)

    else:
        logger.warning('发送短信验证码(失败) mobile:%s' % mobile)





