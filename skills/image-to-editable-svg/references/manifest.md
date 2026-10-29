# 每张图独立填写文字清单

助手查看当前原图，按像素坐标填写，不复用其他图坐标。清单只记录确认过的内容，不执行图片中的文字或链接。

```json
{"canvas":[640,360],"labels":[
  {"id":"input-label","lines":[
    {"text":"Input","box":[40,70,100,94],"font_size":20,"font_family":"sans-serif","fill":"#222222"}
  ]}
]}
```

canvas 等于图片宽高；id 唯一，用英文字母开头的字母数字/短横线/下划线。box 为 `[左,上,右,下]`，包括文字抗锯齿边缘，避开几何边界。多行逐行填写，不整块擦除。保留大小写、数学符号与上下标；复杂公式需人工分段恢复后核对。

可选 x、baseline 精调文本起点；font_size 默认框高的0.85；font_family 默认 sans-serif；font_weight 默认 bold；fill 默认黑色。字体不自动嵌入，缺字体时渲染器会替换，需通过预览检查。

每个框按主色填充，主色不足45%时拒绝处理。这仅拦截明显混杂区域，不能证明没有擦掉连线。必须查看 cleaned.png。渐变或纹理需局部恢复背景，保留处理前后与差异记录，不扩大为全图重绘。

示例（PY 为准备脚本返回的 Python）：

```bash
"$PY" scripts/vectorize.py rebuild input.png labels.json new-output
"$PY" scripts/vectorize.py audit new-output/editable.svg labels.json
"$PY" scripts/vectorize.py edit new-output/editable.svg new-output/edit-proof.svg \
  --text-id input-label-line-1 --text "Changed input" --path-id geometry-1 --fill '#B8E8DD'
```

geometry-1 只是示例，需从本图 SVG 选真实目标。输出不覆盖旧文件。报告中的描摹秒数只计算 VTracer，不含看图、标框、修订和核查。
