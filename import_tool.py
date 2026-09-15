# import_tool.py
# ==============================================================================
# 模块名称: 项目上下文生成器 (Project Context Packer)
# 功能描述:
#   1. 扫描当前文件夹下的所有代码文件。
#   2. 忽略 .venv, __pycache__, .git 等无关文件夹。
#   3. 生成一个名为 PROJECT_FULL_CONTEXT.md 的文件。
#   4. 将该生成的文件发送给 AI，AI 就能拥有你项目的"上帝视角"。
#
# 修复说明:
#   - 修复了因为代码中包含 markdown 标记导致复制粘贴时报错的问题。
# ==============================================================================

import os
import time


class ProjectPacker:
    def __init__(self):
        # 1. 定义要忽略的文件夹和文件类型
        self.IGNORE_DIRS = {
            '.venv', 'venv', 'env', '.git', '.idea', '.vscode',
            '__pycache__', 'build', 'dist', 'node_modules',
            'htmlcov', '.pytest_cache'
        }

        self.IGNORE_EXTENSIONS = {
            '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin',
            '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',
            '.pdf', '.doc', '.docx', '.zip', '.tar', '.gz'
        }

        # 定义要包含的文件扩展名
        self.INCLUDE_EXTENSIONS = {
            '.py', '.md', '.txt', '.json', '.yaml', '.yml',
            '.html', '.css', '.js', '.qss', '.xml', '.ini'
        }

        # 输出文件名
        self.OUTPUT_FILE = "PROJECT_FULL_CONTEXT.md"

    def is_ignored(self, path):
        """判断路径是否应该被忽略"""
        parts = path.split(os.sep)
        for part in parts:
            if part in self.IGNORE_DIRS:
                return True

        _, ext = os.path.splitext(path)
        if ext.lower() in self.IGNORE_EXTENSIONS:
            return True

        return False

    def is_included(self, filename):
        """判断文件是否是我们需要读取的代码文件"""
        _, ext = os.path.splitext(filename)
        return ext.lower() in self.INCLUDE_EXTENSIONS

    def generate_tree(self, startpath):
        """生成目录树结构字符串"""
        # 使用变量拼接，避免Markdown渲染错误
        fence = "`" * 3
        tree_str = f"## 1. 项目目录结构 (Project Tree)\n\n{fence}text\n"
        tree_str += f"📂 {os.path.basename(os.getcwd())}/\n"

        for root, dirs, files in os.walk(startpath):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]

            level = root.replace(startpath, '').count(os.sep)
            indent = '│   ' * (level)
            subindent = '│   ' * (level + 1)

            if root != startpath:
                tree_str += f"{indent}📂 {os.path.basename(root)}/\n"

            for f in files:
                if not self.is_ignored(os.path.join(root, f)):
                    tree_str += f"{subindent}{f}\n"

        tree_str += f"{fence}\n\n"
        return tree_str

    def generate_content(self, startpath):
        """读取所有文件的具体内容"""
        content_str = "## 2. 文件详细内容 (File Contents)\n\n"
        # 同样使用变量拼接反引号
        fence = "`" * 3

        file_count = 0

        for root, dirs, files in os.walk(startpath):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]

            for file in files:
                file_path = os.path.join(root, file)

                if not self.is_ignored(file_path) and self.is_included(file):
                    rel_path = os.path.relpath(file_path, startpath)

                    if file == self.OUTPUT_FILE or file == "import_tool.py":
                        continue

                    print(f"正在读取: {rel_path} ...")

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()

                        _, ext = os.path.splitext(file)
                        lang = ext.replace('.', '')
                        if lang == 'py': lang = 'python'

                        # 构建 Markdown 格式的代码块 (拆分写法，防止语法错误)
                        content_str += f"### 📄 `{rel_path}`\n\n"
                        # 重点修复：这里不要直接写三个反引号，用变量 fence 代替
                        content_str += f"{fence}{lang}:{rel_path}\n"
                        content_str += file_content
                        content_str += f"\n{fence}\n\n---\n\n"
                        file_count += 1

                    except Exception as e:
                        print(f"❌ 无法读取文件 {rel_path}: {e}")

        print(f"\n✅ 共处理了 {file_count} 个代码文件。")
        return content_str

    def run(self):
        """执行主逻辑"""
        current_dir = os.getcwd()
        print(f"开始扫描项目: {current_dir}")
        print("请稍候...\n")

        header = f"# 项目上下文文档\n生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        header += "> 注意：此文档包含项目的完整代码细节。请将此文件发送给 AI 助手以便进行代码修改。\n\n"

        tree_section = self.generate_tree(current_dir)
        content_section = self.generate_content(current_dir)

        full_text = header + tree_section + content_section

        try:
            with open(self.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f"\n🎉 成功生成文件: {self.OUTPUT_FILE}")
            print(f"📂 文件位置: {os.path.join(current_dir, self.OUTPUT_FILE)}")
            print("\n👉 下一步: 请将生成的 .md 文件直接上传给 AI。")
        except Exception as e:
            print(f"❌ 写入文件失败: {e}")


if __name__ == "__main__":
    packer = ProjectPacker()
    packer.run()