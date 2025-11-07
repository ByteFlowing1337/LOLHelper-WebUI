"""
LOLHelper WebUI 主入口文件
模块化版本
"""
from flask import Flask
from flask_socketio import SocketIO
import threading
import webbrowser

from config import HOST, PORT
from routes import page_bp, data_bp
from websocket import register_socket_events
from utils import get_local_ip


def create_app():
    """
    创建并配置Flask应用
    
    Returns:
        tuple: (app, socketio)
    """
    # 初始化Flask应用
    app = Flask(__name__)
    
    # 注册蓝图
    app.register_blueprint(page_bp)  # 页面渲染路由
    app.register_blueprint(data_bp)  # 数据 API 路由
    
 
    
    # 初始化SocketIO
    # 打包环境使用 threading 模式，并排除 eventlet/gevent
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*",
        async_mode='threading',
        logger=False,
        engineio_logger=False
    )
    
    # 注册WebSocket事件
    register_socket_events(socketio)
    
    return app, socketio


def open_browser_delayed(url):
    """
    延迟打开浏览器
    
    Args:
        url: 要打开的URL
        delay: 延迟秒数
    """
    def _open():
        print(f"尝试在浏览器中打开: {url}")
        webbrowser.open(url)
    
    threading.Timer(0,_open).start()


def main():
    """主函数"""
    # 创建应用
    app, socketio = create_app()
    
    # 获取本地IP
    local_ip = get_local_ip()
    server_address = f'http://{local_ip}:{PORT}'
    
    # 延迟打开浏览器
    open_browser_delayed(server_address)
    
    # 输出启动信息  
    print("Lcu UI 已启动！")
    print(f"本机访问地址: http://127.0.0.1:{PORT}")
    print(f"局域网访问地址: {server_address}")
    # 启动服务器
    socketio.run(app, host=HOST, port=PORT)


if __name__ == '__main__':
    main()
