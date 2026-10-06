# 输入与命令

`<python>` 表示已确认版本不低于 3.10 的解释器；macOS/Linux 通常是 `python3`，Windows 通常是 `py -3`。`<skill>` 表示安装目录。参数使用实际路径，并为带空格的路径加引号。

## 提示词输入

把以下结构写入任务输出目录的 `brief.json`。自然语言字段使用 English，便于直接传给图像工具。

```json
{
  "mode": "artwork",
  "subject": "a folded paper moon",
  "material": "soft ivory paper",
  "palette": ["#24364B", "#FFF1D6"],
  "details": ["one curved fold", "one small star"]
}
```

必填字段是 `subject`、`material`、`palette`、`details`。配色必须是 1–5 个六位色号，细节必须是 2–3 条。`mode` 可选 `artwork` 或 `foreground`，默认前者。可选 `style` 替换主题段的默认风格；前景模式应保持基础形状，不写入模拟玻璃效果。其他字段会被拒绝。

```text
<python> <skill>/scripts/icon_tools.py prompt <output>/brief.json --out <output>/prompt.txt
```

命令只组装提示词，不调用图像服务。输出已存在时拒绝覆盖，改用新的候选目录或版本文件名。生成后把提示词交给宿主图像工具。

## 图片检查

```text
<python> <skill>/scripts/icon_tools.py check <output>/icon.png
<python> <skill>/scripts/icon_tools.py check <output>/foreground.png --mode foreground
```

检查依赖 Pillow；先用选定解释器执行 `-c "import PIL; print(PIL.__version__)"`。没有 Pillow 时优先发现宿主已有的图像运行环境。确需安装时，说明这是本地图片检查依赖并取得安装授权，再放入独立环境；不要改变系统解释器。

缺少依赖且无法获得环境时仍可交付图片，但 `qa.md` 必须标记像素检查待完成。不得称整体检查通过。

命令输出 JSON，成功退出码为 0，失败非 0。`status=pass` 只代表尺寸、文件格式与透明度符合当前模式；`visual_review=pending` 始终保留，目视检查另行记录。

前景检查只要求存在完全透明像素和可见内容，不能证明背景已干净移除、主体没有被裁切或图层已对齐。整图检查也不能识别画进不透明图片内的白框或假圆角。

## 恢复

提示词输入错误时修复 `brief.json` 后重试。图像工具失败时保留提示词、参考图和已完成的候选，报告失败步骤。尺寸不符时优先请求工具按指定尺寸导出；只在用户授权或任务允许时重采样交付副本，并披露处理，不拉伸非正方形源图。

## 回归测试

```text
<python> -m unittest discover -s <skill>/tests
```

没有 Pillow 时图片测试会跳过；只通过提示词测试不代表图片检查能力已验证。
