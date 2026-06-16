# better-word

`better-word` 是一个 Codex skill，用 AI 生成课程报告，并按目标文件选择最稳的排版路线：PDF 走 LaTeX，Word 走原生 `.docx` 模板。

核心思路是：不要把所有场景都塞进 LaTeX。只交 PDF 时，用 LaTeX 获得稳定排版；必须交 Word 且要像官方模板时，直接复制并填充原始 `.docx` 模板，避免 LaTeX 转 Word 带来的格式损失。

## 适合做什么

- 从学校官方 Word、PDF 或截图模板中提取页边距、字体字号、行距、标题层级、页眉页脚、图表编号和参考文献规则。
- 生成可复用的中文课程报告 LaTeX 模板。
- 只需要 PDF 时，让 AI 按固定模板写 `.tex`。
- 需要 Word 时，基于官方 `.docx` 模板生成新 `.docx`，尽量保留原始样式、页眉页脚、编号和节设置。
- 编译并检查 PDF，减少 Word 合并、图片拖动、样式联动导致的格式问题。

## 安装

把这个仓库放到 Codex skills 目录下，目录名保持为 `better-word`。

在 GitHub 页面点击 `Code` 复制仓库地址，然后运行：

Windows：

```powershell
git clone <复制的仓库地址> "$env:USERPROFILE\.codex\skills\better-word"
```

macOS/Linux：

```bash
git clone <复制的仓库地址> ~/.codex/skills/better-word
```

如果已经下载为压缩包，也可以手动解压到对应目录：

```text
~/.codex/skills/better-word
```

或 Windows：

```text
C:\Users\<你的用户名>\.codex\skills\better-word
```

## 最短用法

只需要告诉 Codex 三件事：

1. 模板文件：最好是官方 `.docx`，只有 PDF/截图也可以。
2. 报告内容：主题、提纲、资料或已有草稿。
3. 目标格式：`PDF`、`Word` 或 `both`。

如果目标是 Word 且要求“看起来像官方模板”，必须提供原始 `.docx` 模板。仅靠截图或 LaTeX 转 Word，无法稳定做到以假乱真。

## 使用示例

分析学校模板：

```text
Use $better-word to analyze this official course report template and extract the formatting rules.
```

生成 PDF：

```text
Use $better-word to write a course report about <主题>. Target output: PDF.
```

生成高保真 Word：

```text
Use $better-word to write a course report about <主题>. Target output: Word. Use the official .docx template as the formatting source of truth.
```

同时生成 Word 和 PDF：

```text
Use $better-word to write a course report about <主题>. Target output: both Word and PDF. Word fidelity is more important than LaTeX typography.
```

## 依赖

必须：

- 支持 Codex skills 的 Codex 环境。

可选：

- 本地 TeX 工具链：TeX Live 或 MiKTeX。
- 编译命令：`latexmk -xelatex`，或运行 `xelatex` 两次。
- Word 生成：官方 `.docx` 模板；可选 `python-docx`、直接 OOXML 编辑、`docxtpl`。
- 近似 Word 导出：Pandoc；适合草稿，不适合以假乱真的模板还原。
- 在线替代方案：Overleaf，建议选择 XeLaTeX 或 LuaLaTeX 编译器。

中文报告建议优先使用 XeLaTeX 或 LuaLaTeX。模板中默认使用 `ctexart`，适合作为中文课程报告的起点；具体学校字体、字号和页边距应按官方模板审计结果调整。

高保真 `.docx` 不建议从 LaTeX/Pandoc 反向转换。Pandoc 可以做可编辑草稿，但很难完整还原 Word 模板里的页眉页脚、节、编号、标题页和样式继承。真正要像官方模板，应以原始 `.docx` 为源文件，复制后填充内容。

## 仓库结构

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   └── course-report-template.tex
├── references/
│   ├── template-analysis-checklist.md
│   └── word-export.md
├── LICENSE
└── README.md
```

## 验证

在本仓库根目录运行 skill 校验：

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .
```

如果本机安装了 TeX 工具链，可以复制模板到临时目录后编译：

```powershell
Copy-Item .\assets\course-report-template.tex $env:TEMP\better-word-template.tex
Push-Location $env:TEMP
latexmk -xelatex -interaction=nonstopmode better-word-template.tex
Pop-Location
```

如果只是需要近似可编辑 Word，安装 Pandoc 后可以导出：

```powershell
pandoc main.tex --from latex --to docx --output main.docx --reference-doc reference.docx
```

## 许可证

MIT
