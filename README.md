# 六子棋程序对战系统

这是一个使用 Python 标准库实现的 19×19 六子棋程序。启动后通过主菜单进入比赛模式或游玩模式。比赛模式可监听 TCP 端口并连接另一个棋手程序；游玩模式支持真人对真人和真人对程序。

## 运行

```powershell
python main.py
```

可选参数：

```powershell
python main.py --theme themes/default/theme.json
```

## 比赛模式

在主菜单进入“比赛模式”，设置监听地址、端口和棋钟，然后点击“开始监听并准备”。另开终端运行附带的示例对手：

```powershell
python examples/remote_bot.py --host 127.0.0.1 --port 8765
```

双方使用一行一个 JSON 对象的 TCP 协议，消息包括 `GAME_START`、`YOUR_TURN`、`TURN`、`OPPONENT_TURN` 和 `GAME_OVER`。

## 更换皮肤

复制 `themes/default`，修改 `theme.json`。可以修改颜色，也可以为 `black_image`、`white_image` 和 `board_image` 指定 PNG 文件。棋子图片建议使用透明背景正方形 PNG。

## 接入正式棋手

实现 `six_stones.players.Player` 的 `choose_turn()` 方法即可替换内置棋手。该方法一次返回本回合全部坐标，裁判统一验证和提交。
