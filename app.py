"""
LOLHelper WebUI 主入口文件
模块化版本
"""
from flask import Flask
from flask_socketio import SocketIO
import threading
import webbrowser

from config import SECRET_KEY, HOST, PORT
from routes import api_bp
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
    app.config['SECRET_KEY'] = SECRET_KEY
    
    # 注册蓝图
    app.register_blueprint(api_bp)
    
 
    
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


def open_browser_delayed(url, delay=0.5):
    """
    延迟打开浏览器
    
    Args:
        url: 要打开的URL
        delay: 延迟秒数
    """
    def _open():
        print(f"尝试在浏览器中打开: {url}")
        webbrowser.open(url)
    
    threading.Timer(delay, _open).start()


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
    print("=" * 60)
    print("🎮 LOLHelper WebUI 已启动！")
    print("=" * 60) 
    print(f"📍 本机访问地址: http://127.0.0.1:{PORT}")
    print(f"🌐 局域网访问地址: {server_address}")
    print(f"💡 提示: 请确保防火墙已允许端口 {PORT}")
    print("=" * 60)
    
    # 启动服务器
    socketio.run(app, host=HOST, port=PORT)


if __name__ == '__main__':
    main()
