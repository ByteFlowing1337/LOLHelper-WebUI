"""
React SPA 静态文件路由
"""
from flask import Blueprint, send_from_directory
import os

react_bp = Blueprint('react', __name__)

@react_bp.route('/', defaults={'path': ''})
@react_bp.route('/<path:path>')
def serve_react(path):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    react_root = os.path.join(project_root, 'static', 'react')

    if not os.path.exists(react_root):
        return (
            '<h1>React 前端未构建</h1>'
            '<p>请运行构建命令后再访问：</p>'
            '<pre>cd frontend && npm install && npm run build</pre>'
            '<p>开发模式：</p>'
            '<pre>cd frontend && npm run dev</pre>'
        ), 404

    file_path = os.path.join(react_root, path)
    if path and os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(react_root, path)

    return send_from_directory(react_root, 'index.html')
