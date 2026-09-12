# 皮肤替换

复制 `default` 文件夹并修改 `theme.json` 即可创建新皮肤。

- `black_image`、`white_image`：棋子 PNG 文件路径，推荐透明背景正方形图片。
- `board_image`：棋盘背景 PNG 文件路径。
- `board_color`、`board_alt_color`：草坪格子的两种交替底色。
- `grass_highlight_color`：每格绒毛高光颜色。
- 图片路径相对于对应 `theme.json` 所在目录。
- 图片字段留空时，程序会用配置颜色绘制默认的黑猫头与白狗头棋子。

启动时使用 `python main.py --theme themes/你的主题/theme.json`。
