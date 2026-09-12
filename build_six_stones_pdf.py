from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
import os

OUT = os.path.join('output', 'pdf', 'six_stones_match_design.pdf')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
font = r'C:\Windows\Fonts\msyh.ttc'
pdfmetrics.registerFont(TTFont('MSYH', font, subfontIndex=0))
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='CN', parent=styles['BodyText'], fontName='MSYH', fontSize=10.2, leading=16, spaceAfter=6))
styles.add(ParagraphStyle(name='H1CN', parent=styles['Heading1'], fontName='MSYH', fontSize=16, leading=22, textColor=colors.HexColor('#17365D'), spaceBefore=10, spaceAfter=8))
styles.add(ParagraphStyle(name='H2CN', parent=styles['Heading2'], fontName='MSYH', fontSize=12.5, leading=18, textColor=colors.HexColor('#1F4E79'), spaceBefore=8, spaceAfter=5))
styles.add(ParagraphStyle(name='TitleCN', parent=styles['Title'], fontName='MSYH', fontSize=23, leading=30, alignment=TA_CENTER, textColor=colors.HexColor('#17365D'), spaceAfter=18))
styles.add(ParagraphStyle(name='SmallCN', parent=styles['BodyText'], fontName='MSYH', fontSize=8.5, leading=12, textColor=colors.grey))
styles.add(ParagraphStyle(name='CodeCN', parent=styles['Code'], fontName='Courier', fontSize=7.8, leading=10))

def P(t, style='CN'): return Paragraph(t, styles[style])
def footer(canvas, doc):
    canvas.saveState(); canvas.setFont('MSYH', 8); canvas.setFillColor(colors.grey)
    canvas.drawString(20*mm, 12*mm, '六子棋比赛系统设计文档')
    canvas.drawRightString(190*mm, 12*mm, f'第 {doc.page} 页')
    canvas.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=20*mm)
story = []
story += [Spacer(1, 28*mm), P('19×19 六子棋程序对战系统', 'TitleCN'), P('比赛版游戏设计文档', 'H2CN'), Spacer(1, 8*mm), P('版本：V1.0　　实现语言：Python　　适用场景：两个独立棋手程序自动对局', 'CN'), PageBreak()]
story += [P('1. 项目目标', 'H1CN'), P('本项目实现一个用于程序对抗赛的六子棋系统。棋盘采用 19×19 规格，黑方首回合落一子，之后黑白双方轮流每回合落两子。横、竖或两条斜线连续六子及以上即获胜；棋盘填满且无人获胜时判和棋。', 'CN'), P('比赛由裁判程序统一负责颜色随机分配、棋盘状态、原子回合验证、棋钟、点位同步及胜负判定。A、B 是两个相互独立的棋手程序，界面可以不同，只通过统一通信协议交换比赛数据。', 'CN')]
story += [P('2. 规则与比赛约定', 'H1CN')]
rules = [['项目','约定'],['棋盘','19×19，列 A-S，行 1-19'],['首回合','随机获得黑方的一方落一子'],['普通回合','双方轮流各落两子'],['原子提交','两颗棋子必须一次性提交；任意一颗非法则整回合无效'],['胜负','连续六子或更长即获胜，长连有效'],['禁手','无禁手，三三、四四等均允许'],['修改限制','成功落子后不可修改、撤回、覆盖或移动'],['和棋','棋盘填满且没有六连']]
t=Table([[P(a,'SmallCN'),P(b,'SmallCN')] for a,b in rules], colWidths=[32*mm,135*mm]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#D9EAF7')),('GRID',(0,0),(-1,-1),0.4,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6)])); story += [t]
story += [P('3. 系统架构', 'H1CN'), P('系统采用裁判服务器加两个棋手客户端的结构。裁判维护唯一的完整棋盘，双方程序不读取对方界面，只接收裁判广播的落子点位。', 'CN'), Preformatted('棋手A程序 ─┐\n            ├── 裁判程序：完整棋盘、计时、规则、同步、结果\n棋手B程序 ─┘', styles['CodeCN']), P('建议使用 TCP Socket 传输 JSON 行消息。这样可以支持同机对战，也可以扩展到局域网双机比赛。', 'CN')]
story += [P('4. 比赛状态机', 'H1CN'), Preformatted('START → 随机分配颜色 → BLACK_FIRST(1子)\n      → 轮到当前棋手 YOUR_TURN(n子)\n      → 接收完整回合 → 临时棋盘验证\n      → 拒绝并重提 / 原子提交并广播\n      → 检查六连、超时、和棋\n      → 切换棋手或 GAME_OVER', styles['CodeCN']), P('裁判收到完整坐标列表后，先复制棋盘进行验证；只有两颗棋子全部合法，才一次性替换正式棋盘。验证期间正式棋盘不改变，也不会向对方发送中间状态。', 'CN')]
story += [P('5. 通信协议', 'H1CN')]
proto = [['消息','方向','示例'],['GAME_START','裁判→棋手','{"color":"BLACK","board_size":19}'],['YOUR_TURN','裁判→当前棋手','{"stones":2,"time_left":597.4}'],['TURN','棋手→裁判','{"moves":["J10","K11"]}'],['TURN_ACCEPTED','裁判→双方','{"color":"WHITE","moves":["J10","K11"]}'],['TURN_REJECTED','裁判→当前棋手','{"reason":"位置已被占用"}'],['GAME_OVER','裁判→双方','{"winner":"BLACK"}']]
t=Table([[P(a,'SmallCN'),P(b,'SmallCN'),P(c,'SmallCN')] for a,b,c in proto], colWidths=[32*mm,32*mm,103*mm]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#D9EAF7')),('GRID',(0,0),(-1,-1),0.4,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP') ])); story += [t, P('每次成功提交后，裁判向双方广播本回合全部点位。双方程序据此更新本地棋盘；本地状态与裁判冲突时应记录错误并停止决策，不得自行猜测。', 'CN')]
story += [P('6. Python 核心模块', 'H1CN'), P('推荐目录如下：', 'CN'), Preformatted('six_stones_match/\n├── referee.py       # 裁判服务器\n├── board.py         # 19×19棋盘，只允许落子\n├── rules.py         # 六连、和棋判断\n├── turn.py          # 原子回合验证与提交\n├── clock.py         # 双方棋钟\n├── protocol.py      # JSON通信\n├── player_a.py      # 我方棋手\n├── player_b_test.py # 测试对手\n└── replay.py        # 棋局复盘', styles['CodeCN'])]
story += [P('六连检查只需扫描横、竖、主对角线和副对角线四个方向，判断连续数量是否大于等于 6。棋盘只提供 place() 操作，禁止覆盖、删除和移动。', 'CN'), P('7. 棋钟与超时', 'H1CN'), P('双方各有独立棋钟。轮到某方时启动该方计时器；裁判收到完整回合并完成处理后停止计时。思考、生成两颗点位、通信和非法回合重提时间均计入本方用时。剩余时间小于等于零时立即判负。', 'CN'), Preformatted('clock.start()\nreceive complete TURN\nclock.stop()\nif clock.remaining() <= 0: winner = opponent', styles['CodeCN'])]
story += [P('8. 我方棋手自动决策', 'H1CN'), P('我方程序收到 YOUR_TURN 后，根据本地完整同步棋盘自动计算一颗或两颗点位，并在一次消息中提交。AI 可以分阶段实现：先做随机落子，再加入立即成六、阻止对手成六、五连、活四、活三和中心/邻近度评分，最后使用候选点筛选加 Minimax/Negamax 搜索。', 'CN'), P('建议候选点只取已有棋子附近 2 格以内的位置，显著降低两子组合的搜索分支。', 'CN')]
story += [P('9. 日志、复盘与测试', 'H1CN'), P('每个成功回合追加写入不可变棋谱，记录回合号、颜色、两颗点位、时间和剩余用时。非法回合只写入调试日志，不写入正式棋谱。', 'CN'), P('测试重点包括：黑方首回合数量、同回合重复点、整回合原子失败、长连胜利、棋盘填满和棋、超时判负、颜色随机分配、双方点位广播一致性。', 'CN')]
story += [P('10. 实施计划', 'H1CN'), P('第一阶段完成棋盘、坐标转换和六连判断；第二阶段完成裁判服务器、JSON 协议和原子回合；第三阶段加入棋钟、超时和日志；第四阶段实现随机/启发式棋手并进行自动对局；第五阶段加入图形界面与复盘工具。', 'CN'), P('最终比赛时只启动裁判程序、我方棋手程序和对方棋手程序。颜色由裁判随机决定，双方按照协议自动完成整局比赛。', 'CN')]
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
