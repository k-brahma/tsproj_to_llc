"""
PySimpleGUI で作られたフォーム
ファイル選択ダイアログと、実行ボタンがある。

実行ボタンで、 config_utils.py の関数 process を呼び出す。
"""
import json

import PySimpleGUI as sg

from config_utils import create_opencv_config, create_llc_config
from process import cut_video_segments, create_thumbnail_files


def main():
    """
    ファイル選択ダイアログを表示する。
    """
    # ファイル選択ダイアログのレイアウト
    layout = [
        [sg.Text('ファイルを選択してください')],
        [sg.InputText(), sg.FileBrowse()],
        [sg.Checkbox('Create llc file', default=True)],
        [sg.Checkbox('Create Movie immediately', default=False)],
        [sg.Checkbox('Create Thumbnail', default=False)],
        [sg.Submit(button_text='実行')],
    ]

    # ファイル選択ダイアログの表示
    window = sg.Window('ファイル選択', layout)

    # ファイル選択ダイアログのイベントループ
    while True:
        event, values = window.read()
        if event is None:
            break
        if event == '実行':
            execute_process(values[0], values[1], values[2], values[3], )
            break

    window.close()


def execute_process(file_path, create_llc=True, create_movie=False, create_thumbnail=False):
    """
    UIからの入力を受け取って、処理を実行する

    :param file_path: tscproj または json ファイルのパス
    :param create_llc: True のとき、llc ファイルを作成する
    :param create_movie: True のとき、すぐに opencv を使って動画を分割する
    :param create_thumbnail: True のとき、サムネイルを作成する
    """
    # file_path のファイルの拡張子が .tscproj のとき、 .json のときで処理を分ける。
    # .json のときは、それを読み込んで opencv_dict とする
    if file_path.endswith('.tscproj'):
        opencv_dict = create_opencv_config(file_path)
    else:
        opencv_dict = json.load(open(file_path, encoding='utf8'))

    if create_llc:
        create_llc_config(opencv_dict)

    if create_movie:
        cut_video_segments(opencv_dict, create_thumbnail)

    if create_thumbnail:
        create_thumbnail_files(opencv_dict)


if __name__ == "__main__":
    main()
