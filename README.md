# assignment-docx-filler

一个面向大学编程作业的 Codex Skill：把短代码、文字答案和用户提供的真实截图填入教师原始 Word 模板，同时尽量不破坏题目顺序、边框、样式、页眉页脚、编号和节设置。

## 当前状态

当前仓库处于 **阶段 0：产品与技术设计完成，确定性脚本尚未实现**。

仓库已经包含完整的领域定义、架构决策、数据契约、脚本接口和验收标准，但暂时不应声称能自动完成高保真 DOCX 填充。下一阶段将按 [DESIGN.md](./DESIGN.md) 实现和验证脚本。

## 为什么需要这个项目

常见编程作业模板如下：

```text
第 1 题
题目描述……

代码：
[填写代码]

运行结果：
[插入真实截图]
```

直接让 AI 重新生成 Word，容易打乱原有顺序、边框、编号和分页。LaTeX 或 Pandoc 可以生成新文档，但不能可靠还原教师现有 DOCX。

本项目选择另一条路线：**复制教师原模板，只在明确的作答区域内定点修改 OOXML。**

## 第一版体验

用户只需要提供：

1. 教师原始 `.docx`；没有 DOCX 时可提供 PDF 作为后备模板。
2. 每道题的代码或文字答案，例如 `q1.py`、`q2.cpp`。
3. 用户自己截取的真实运行截图，例如 `q1-1.png`、`q1-2.png`。

Skill 将执行：

```text
模板校验
→ 识别题目与“代码/运行结果”锚点
→ 映射答案材料
→ 只确认冲突项
→ 生成模板副本
→ Word 渲染与保真检查
→ 输出提交文件和诊断报告
```

## 产品边界

第一版：

- Windows + 已安装 Microsoft Word。
- 标签型 DOCX 模板，答案位于“代码：”“运行结果：”等锚点之后。
- 任意纯文本代码语言，不执行、不重构、不补注释。
- 用户提供 PNG/JPG/JPEG 截图，每题可有多张。
- 允许答案导致换页，但不允许作答区域外的模板结构丢失。
- PDF 仅作后备输入；默认填充并输出 PDF，不承诺 PDF 转高保真 DOCX。

第一版不支持：

- 表格答案槽、文本框和复杂公式。
- 加密 DOCX、DOCM 和未处理的修订模式。
- 自动运行代码或生成伪造截图。
- 跨平台高保真 Word 渲染。
- 将 LaTeX、Pandoc 或 HTML 转换作为 DOCX 主路径。

## 技术方向

- `lxml`：OOXML 定点读写与结构比较。
- `python-docx`：常规样式、节和尺寸读取。
- `pywin32`：Microsoft Word COM 渲染。
- `Pillow`：图片处理与视觉检查。
- `PyMuPDF`：PDF 后备模板分析和填充。
- `pytest`：fixture、集成和回归测试。

详细设计见 [DESIGN.md](./DESIGN.md)。核心术语见 [CONTEXT.md](./CONTEXT.md)。

## 调研依据

- [Microsoft Word 内容控件](https://learn.microsoft.com/en-us/office/client-developer/word/content-controls-in-word)：通过受控区域构建结构化文档。
- [docxtpl](https://github.com/elapouya/python-docx-template)、[docxtemplater](https://github.com/open-xml-templating/docxtemplater)、[Carbone](https://github.com/carboneio/carbone)：保留模板并注入数据的开源实现。
- [AutoDocX](https://github.com/SHAYANZAWAR/AutoDocX)、[Lab Record Maker](https://github.com/deependrasinghsolanki03-alt/lab-record-maker)：代码作业 Word 自动化的直接参考。
- [DocLayNet](https://arxiv.org/abs/2206.01062)、[PubLayNet](https://doi.org/10.1109/icdar.2019.00166)、[LayoutParser](https://arxiv.org/abs/2103.15348)：PDF 后备模式的版面识别研究基础。

## 安装

当前版本主要用于设计评审。仍可安装 Skill 契约以供 Codex 读取：

```powershell
git clone https://github.com/styleliyu/assignment-docx-filler.git "$env:USERPROFILE\.codex\skills\assignment-docx-filler"
```

调用示例：

```text
Use $assignment-docx-filler to fill this programming assignment template.
Use my code files and screenshots, preserve the original DOCX formatting,
and ask only when an answer region is ambiguous.
```

## 文档

- [设计文档](./DESIGN.md)
- [领域词汇](./CONTEXT.md)
- [ADR 0001：DOCX 原生修改和 Word 验证](./docs/adr/0001-use-docx-native-word-validation.md)
- [ADR 0002：PDF 仅作为后备输入](./docs/adr/0002-pdf-is-fallback-only.md)
- [模板分析清单](./references/template-analysis-checklist.md)
- [DOCX 保真规则](./references/docx-fidelity.md)

## 许可证

MIT
