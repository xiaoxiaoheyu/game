# 皮肤替换

复制 `default` 文件夹并修改 `theme.json` 即可创建新皮肤。

- `black_image`、`white_image`：棋子 PNG 文件路径，推荐透明背景正方形图片。
- `board_image`：棋盘背景 PNG 文件路径。
- 图片路径相对于对应 `theme.json` 所在目录。
- 图片字段留空时使用配置中的颜色绘制。

启动时使用 `python main.py --theme themes/你的主题/theme.json`。

