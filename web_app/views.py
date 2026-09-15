"""
文件路径: web_app/views.py
功能: 视图层统一入口，聚合各个子模块，确保对外接口兼容性。
注意：现在具体的逻辑代码已经迁移到了同目录下的 views_*.py 文件中。
"""

# 从子模块导入接口，保持 main_web.py 的调用兼容性
from .views_upload import view_upload
from .views_processing import view_processing
from .views_result import view_result
from .views_components import render_footer

# 导出以供外部调用
__all__ = ['view_upload', 'view_processing', 'view_result', 'render_footer']