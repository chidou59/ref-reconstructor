import sys
import os

# 尝试导入 Streamlit CLI 工具
try:
    from streamlit.web import cli as stcli
except ImportError:
    # 兼容旧版本 Streamlit
    try:
        from streamlit import cli as stcli
    except ImportError:
        print("❌ 未检测到 Streamlit，请先确保已安装: pip install streamlit")
        sys.exit(1)


def main():
    """
    此脚本用于在 PyCharm/VSCode 中直接点击 'Run' 启动 Streamlit 应用。
    它模拟了在命令行执行 `streamlit run main_web.py` 的行为。
    """
    # 1. 获取当前脚本所在的绝对路径
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. 指定您的主程序文件名
    app_script_name = "main_web.py"
    app_script_path = os.path.join(base_dir, app_script_name)

    # 检查文件是否存在
    if not os.path.exists(app_script_path):
        print(f"❌ 找不到主程序文件: {app_script_path}")
        print("请确保 run_app.py 和 main_web.py 在同一个文件夹下。")
        return

    # 3. 构造启动参数
    # 这相当于在终端手动输入: streamlit run "C:\Path\To\main_web.py"
    sys.argv = [
        "streamlit",
        "run",
        app_script_path,
        "--global.developmentMode=false"  # 关闭开发模式提示
    ]

    print(f"🚀 正在启动参考文献重构大师...")
    print(f"📂 加载文件: {app_script_path}")
    print("--------------------------------------------------")

    # 4. 启动 Streamlit
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()