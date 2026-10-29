"""邮箱有效性验证：格式检查 + MX 记录检查"""
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# 格式正则
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
)


def validate_format(email: str) -> bool:
    """检查邮箱格式是否合法"""
    if not email:
        return False
    return bool(EMAIL_PATTERN.match(email.strip()))


def check_mx(email: str, timeout: float = 3.0) -> bool:
    """检查邮箱域名是否有 MX 邮件服务器"""
    try:
        import dns.resolver
        domain = email.split("@")[-1]
        if not domain or "." not in domain:
            return False
        resolver = dns.resolver.Resolver()
        resolver.lifetime = timeout
        resolver.timeout = timeout
        answers = resolver.resolve(domain, "MX")
        return len(answers) > 0
    except ImportError:
        logger.warning("dnspython 未安装，跳过 MX 检查")
        return True  # 没有 dnspython 时保守返回 True
    except Exception as e:
        logger.debug(f"MX 检查失败 {email}: {e}")
        return False


def validate_email(email: str, do_mx_check: bool = True) -> Tuple[int, str]:
    """
    综合验证邮箱
    返回 (评分, 说明):
      2 = 格式正确 + MX 存在（强有效）
      1 = 格式正确但 MX 不确定（弱有效）
      0 = 格式错误
    """
    if not validate_format(email):
        return 0, "格式错误"
    if do_mx_check:
        if check_mx(email):
            return 2, "格式正确 + MX 验证通过"
        else:
            return 1, "格式正确但 MX 未找到"
    return 1, "格式正确（未检查 MX）"
