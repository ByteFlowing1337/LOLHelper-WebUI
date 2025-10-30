"""
网络工具模块
"""
import socket


def get_local_ip():
    """
    获取本地局域网（内网）IP地址
    
    Returns:
        str: IP地址，失败时返回 '127.0.0.1'
    """
    try:
        # 创建一个UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 尝试连接一个外部地址（例如 Google DNS），但数据不会真正发送
        # 这一步是为了让操作系统选择一个合适的网络接口，从而获取到对应的内网IP
        s.connect(('10.255.255.255', 1))
        # 获取socket连接的本机地址
        ip_address = s.getsockname()[0]
    except Exception:
        # 如果获取失败，则使用本地回环地址
        ip_address = '127.0.0.1'
    finally:
        s.close()
    return ip_address
