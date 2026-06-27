# assignment-docx-filler

一个面向大学编程作业的 Codex Skill。它把短代码、文字答案和用户提供的真实截图填入教师原始 Word 模板，只修改“代码：”“运行结果：”等作答区域，避免 AI 重建整份 Word 导致顺序、边框、编号和页眉页脚错乱。

## 当前状态

核心流程已经可用：

- 分析标签型 DOCX/PDF 模板并生成槽位映射。
- 按 `q1.py`、`q1-1.png` 等文件名自动匹配材料。
- 直接修改 DOCX 的目标 OOXML 段落，原模板保持不变。
- 插入用户真实截图，保持宽高比并限制到正文宽度。
- 使用 Microsoft Word COM 打开并导出 PDF，执行结构与基础渲染检查。
- PDF 缺省为降级输入，直接输出填充后的 PDF。

真实教师模板差异很大。发布前仍建议使用自己的模板检查一次；表格槽位、文本框、复杂公式、DOCM 和未处理的修订模式暂不支持。

## 安装

环境要求：Windows、Python 3.11+；高保真 DOCX 校验需要本机安装 Microsoft Word。

```powershell
git clone https://github.com/styleliyu/assignment-docx-filler.git "$env:USERPROFILE\.codex\skills\assignment-docx-filler"
Set-Location "$env:USERPROFILE\.codex\skills\assignment-docx-filler"
python -m pip install -r requirements.txt
```

也可以把仓库放在其他位置；作为 Codex Skill 使用时，目录名应保持为 `assignment-docx-filler`。

## 最简单的用法

准备目录：

```text
assignment.docx
answers/
  q1.py
  q2.cpp
screenshots/
  q1-1.png
  q1-2.png
  q2-1.jpg
```

运行一条命令：

```powershell
python scripts/fill_assignment.py assignment.docx `
  --answers answers `
  --screenshots screenshots `
  --output-dir output
```

输出：

```text
output/
  assignment_completed.docx
  diagnostics.json
  work/
    slot-map.json
    locations.json
    template-render.pdf
    submission-render.pdf
```

如果结果为 `needs-confirmation`，先查看提示的槽位和 `slot-map.json`。确认确实可以替换对应普通段落后重新运行：

```powershell
python scripts/fill_assignment.py assignment.docx `
  --answers answers `
  --screenshots screenshots `
  --output-dir output `
  --confirm q1-code
```

`--confirm` 不能绕过表格、文本框等不支持结构。需要在没有 Word 的环境中生成候选文件时可加 `--no-word-render`，诊断报告会明确标记未完成 Word 视觉校验。

## 在 Codex 中使用

```text
Use $assignment-docx-filler to fill this programming assignment template.
Use my code files and screenshots, preserve the original DOCX formatting,
and ask only when an answer region is ambiguous.
```

用户直接给出代码而不是代码文件时，Skill 会先按题号保存为临时纯文本文件。用户内容优先；默认不运行、不重构、不补注释，也不会生成伪造运行截图。

## 支持的模板

第一版适合以下普通正文段落结构：

```text
第 1 题
题目描述……

代码：
[空白段落或已知占位文字]

运行结果：
[空白段落或已知占位文字]
```

支持的代码锚点：`代码`、`源代码`、`程序`、`程序代码`。

支持的截图锚点：`运行结果`、`实验结果`、`执行结果`、`截图`。

PDF 仅在没有 DOCX 时使用。程序会在原 PDF 页面上覆盖答案并输出 `*_completed.pdf`，不会声称能从 PDF 还原高保真 Word。

## 独立命令

单命令编排器内部调用以下入口，调试或人工控制时可以分别执行：

```powershell
python scripts/analyze_template.py assignment.docx --work-dir work
python scripts/map_materials.py work/slot-map.json --answers answers --screenshots screenshots
python scripts/build_submission.py --template assignment.docx --slot-map work/slot-map.json --output output/assignment_completed.docx
powershell -ExecutionPolicy Bypass -File scripts/render_word.ps1 -Input output/assignment_completed.docx -Output work/submission-render.pdf
python scripts/validate_submission.py --template assignment.docx --submission output/assignment_completed.docx --slot-map work/slot-map.json --report output/diagnostics.json
```

## 验证

```powershell
python -m pytest -q
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .
```

自动化测试覆盖 DOCX/PDF 分析、自然排序材料映射、非破坏式构建、危险内容阻断、显式确认续跑、结构诊断和单命令流程。Word COM 仍应使用真实脱敏模板做最终回归。

## 仓库结构

```text
SKILL.md                         Codex 工作流入口
agents/openai.yaml              Skill UI 元数据
scripts/fill_assignment.py      一键编排入口
scripts/assignment_docx_filler/ 核心 Python 实现
references/                     模板分析与保真规则
tests/                          合成 DOCX/PDF 回归测试
DESIGN.md                       产品与技术设计
CONTEXT.md                      领域词汇
```

## 许可证

MIT
