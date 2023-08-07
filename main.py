"""
PySimpleGUI で作られたフォーム
ファイル選択ダイアログと、実行ボタンがある。

実行ボタンで、 process.py の関数 process を呼び出す。
"""

import PySimpleGUI as sg

import process

# ファイル選択ダイアログのレイアウト
layout = [
    [sg.Text('ファイルを選択してください')],
    [sg.InputText(), sg.FileBrowse()],
    [sg.Submit(button_text='実行')]
]

# ファイル選択ダイアログの表示
window = sg.Window('ファイル選択', layout)

# ファイル選択ダイアログのイベントループ
while True:
    event, values = window.read()
    if event is None:
        break
    if event == '実行':
        # process.py の関数 process を呼び出す
        process.process(values[0])
        break

window.close()
