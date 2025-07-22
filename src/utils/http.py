import socket
import asyncio
from urllib.parse import urlparse

async def test_tcp_connectivity(host, port, timeout=3):
    """
    测试 TCP 四层连通性
    
    Args:
        host: 主机地址
        port: 端口号
        timeout: 超时时间（秒）
    
    Returns:
        bool: True 表示连通，False 表示不连通
    """
    try:
        # 使用 asyncio 的 socket 连接
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception as e:
        return False

# 从 URL 中提取 host 和 port
def extract_host_port(url):
    """
    从 URL 中提取 host 和 port
    
    Args:
        url: URL 字符串，如 "http://example.com:8080/path"
    
    Returns:
        tuple: (host, port)
    """
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        return host, port
    except Exception as e:
        return None, None
