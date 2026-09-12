# 六子棋（Connect6）游玩程序

这是一个使用 Python 标准库实现的 19×19 六子棋对弈程序，带图形界面。主菜单进入"游玩模式"，支持**真人与真人**、**真人与程序**两种本地对战方式。

## 运行

```powershell
python main.py
```

可选参数：

```powershell
python main.py --theme themes/default/theme.json
```

## 游玩模式

启动后点击"开始游玩"，选择对战方式：

- **真人 vs 真人**：两位玩家在同一台机器上轮流落子。
- **真人 vs 程序**：一位玩家与内置电脑程序对弈，程序自动计算并落子。

开局时系统随机分配黑白；对局完成或暂停时可将棋谱保存到 `logs` 目录。

## 游戏规则

棋盘采用 19×19 规格，坐标用列字母 A–S 和行数字 1–19 表示。黑方首回合落一子，此后黑白双方轮流每回合各落两子。横、竖或两条斜线连续六子及以上即获胜（长连有效）；棋盘填满且无人获胜时判和棋。规则详情见 `output/pdf/six_stones_rules.pdf`。

## 更换皮肤

复制 `themes/default`，修改 `theme.json`。默认棋子为黑猫头和白狗头；也可以为 `black_image`、`white_image` 和 `board_image` 指定 PNG 文件覆盖默认绘制。棋子图片建议使用透明背景正方形 PNG。

## 界面设计来源

主菜单的渐变按钮、软阴影卡片和轻量互动效果参考了 MIT 许可的 [Uiverse Galaxy](https://github.com/uiverse-io/galaxy)，并针对 Tkinter 与棋盘游戏场景重新实现。

## 自定义棋手

实现 `six_stones.players.Player` 的 `choose_turn()` 方法即可替换内置电脑程序。该方法一次返回本回合全部坐标，由裁判统一验证和提交。
