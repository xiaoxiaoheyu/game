# 六子棋程序对战系统

这是一个使用 Python 标准库实现的 19×19 六子棋比赛程序。裁判随机分配黑白，黑方首回合落一子，之后双方每回合原子提交两子。程序包含棋钟、胜负判断、自动棋手、JSON 棋谱和可替换皮肤。

## 运行

```powershell
python main.py
```

可选参数：

```powershell
python main.py --time 300 --delay 350 --theme themes/default/theme.json
```

## 更换皮肤

复制 `themes/default`，修改 `theme.json`。可以修改颜色，也可以为 `black_image`、`white_image` 和 `board_image` 指定 PNG 文件。棋子图片建议使用透明背景正方形 PNG。

## 接入正式棋手

实现 `six_stones.players.Player` 的 `choose_turn()` 方法即可替换内置棋手。该方法一次返回本回合全部坐标，裁判统一验证和提交。

