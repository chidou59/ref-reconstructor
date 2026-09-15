# Ref Reconstructor

一个本地运行的 Streamlit 工具，用于扫描 Word 文档中的参考文献、补全元数据、统一 GB/T 7714-2015 格式，并生成可下载的修订版文档。

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![CI](https://github.com/chidou59/ref-reconstructor/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 功能

- 上传并解析 `.docx` 文档。
- 识别正文引用与文末参考文献之间的对应关系。
- 通过 Crossref、OpenAlex、Semantic Scholar 等来源补全元数据。
- 可选使用兼容 OpenAI 接口的 Qwen 服务处理困难条目。
- 按 GB/T 7714-2015 重构文献并写回新的 Word 文档。
- 对文件名、路径、大小和临时输出执行安全检查。

## 快速开始

需要 Python 3.10 或更高版本。

```powershell
git clone https://github.com/chidou59/ref-reconstructor.git
cd ref-reconstructor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run main_web.py
```

也可以运行 `python run.py` 启动 Streamlit。可选环境变量列在 `.env.example` 中；默认流程不要求 Qwen 密钥。

## 处理流程

```text
DOCX -> 安全校验 -> 文档解析 -> 引用映射 -> 元数据检索 -> 格式化 -> 新 DOCX
```

详细设计见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)。

## 项目结构

```text
ref-reconstructor/
├─ main_web.py              Streamlit 页面入口
├─ web_app/                 页面组件与业务流程
├─ core/                    DOCX 解析、映射、渲染与安全
├─ engines/                 元数据编排、格式化与数据源
├─ assets/                  公共界面资源
├─ docs/ARCHITECTURE.md      架构说明
└─ requirements.txt         Python 依赖
```

## 隐私与局限

- 上传文档、生成文档和审计日志是本地运行数据，不应提交到 Git。
- 如果部署到远程服务器，文档会发送至该服务器处理，请自行配置访问控制和数据保留策略。
- 第三方元数据可能不完整；投稿前必须人工核对 DOI、作者、卷期和页码。
- 本项目不是排版规范的权威解释，标准文本应以正式发布版本为准。

## 许可证

本项目采用 [MIT License](LICENSE)。
