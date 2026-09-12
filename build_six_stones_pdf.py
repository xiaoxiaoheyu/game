from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
import os

OUT = os.path.join('output', 'pdf', 'six_stones_rules.pdf')
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
    canvas.drawString(20*mm, 12*mm, '六子棋游戏规则文档')
    canvas.drawRightString(190*mm, 12*mm, f'第 {doc.page} 页')
    canvas.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=20*mm)
story = []
story += [Spacer(1, 28*mm), P('六子棋游戏规则', 'TitleCN'), P('Connect6：19×19 双人对弈规则', 'H2CN'), Spacer(1, 8*mm), P('版本：V1.0　　适用场景：本地游玩（真人对真人 / 真人对程序）', 'CN'), PageBreak()]
story += [P('1. 游戏简介', 'H1CN'), P('六子棋（Connect6）是一种两人对弈的连珠类棋类游戏，棋盘为 19×19。黑方先行，此后黑白双方轮流在棋盘上落子，先将己方棋子排成连续六子及以上的一方获胜。', 'CN')]
story += [P('2. 棋盘与坐标', 'H1CN'), P('棋盘由 19 条横线、19 条竖线组成 19×19 的交叉点。列用字母 A–S 表示，行用数字 1–19 表示，每个交叉点用“列字母+行数字”标注，例如最左上角为 A1，最右下角为 S19。', 'CN')]
story += [P('3. 基本规则', 'H1CN')]
rules = [['项目', '约定'], ['棋盘', '19×19，列 A-S，行 1-19'], ['开局', '黑白颜色由系统随机决定，黑方先走'], ['首回合', '黑方首回合落一子'], ['普通回合', '黑白双方轮流各落两子'], ['棋盘空格不足两子时', '本回合落剩余全部空位'], ['落子位置', '必须落在空交叉点上，同一回合并排两点不可重复'], ['修改限制', '成功落子后不可修改、撤回、覆盖或移动']]
t=Table([[P(a,'SmallCN'),P(b,'SmallCN')] for a,b in rules], colWidths=[32*mm,135*mm]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#D9EAF7')),('GRID',(0,0),(-1,-1),0.4,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6)])); story += [t]
story += [P('4. 落子方式', 'H1CN'), P('黑方落第一子后，白方与黑方轮流落子，每方每回合需一次性提交本回合的全部落点。系统对落点逐一验证：位置必须为空且在同回合并排两点不能重复，任何一点不合法则整回合无效，需要重新落子。', 'CN'), P('玩家在棋盘上单击选择落点，选中本回合应落子数后点击“确认本回合”提交。', 'CN')]
story += [P('5. 胜负判定', 'H1CN'), P('当一方在横、竖或两条斜线（主对角线、副对角线）方向上有连续六子及以上时即获胜，连续更多棋子（长连）同样计胜。', 'CN'), Preformatted('''横：───── 连续6子
竖：│ 连续6子
主对角线：╲ 连续6子
副对角线：╱ 连续6子''', styles['CodeCN']), P('系统自动判断并提示获胜方。棋盘上没有禁手，三三、四四等均为合法着法。', 'CN')]
story += [P('6. 和棋情形', 'H1CN'), P('当棋盘上所有交叉点都被填满且双方都未形成连续六子时，对局判定为和棋。', 'CN')]
story += [P('7. 游玩说明', 'H1CN'), P('程序提供两种本地对战方式：', 'CN'), Preformatted('''真人对真人：两位玩家在同一台机器上轮流落子
真人对程序：一名玩家与内置电脑程序对弈''', styles['CodeCN']), P('每方各有独立的棋钟计时，思考时间耗尽的一方判负。对局过程中可以暂停与继续，并可将棋谱保存到 logs 目录以便日后查看。', 'CN')]
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
