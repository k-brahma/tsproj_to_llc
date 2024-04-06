"""　パスと分割タイミングのCSVファイルを渡して直接動画を分割するプログラム ffmpeg 版　"""
import csv
import subprocess
import sys
from pathlib import Path


def convert_to_seconds(time_str):
    """ 文字列形式の時間（'HH:MM:SS'）を秒単位に変換する関数

    :param: time_str: 文字列形式の時間（'HH:MM:SS'）
    """
    hours, minutes, seconds = map(int, time_str.split(':'))
    return hours * 3600 + minutes * 60 + seconds


def get_split_times(csv_path):
    """ CSVファイルから分割タイミングを読み込む関数

    csv ファイルは以下の列を有する。
    ID,ファイル名,タイトル,終了時刻
    このうち、ファイル名と終了時刻を取得する。

    :param: csv_path: CSVファイルのパス
    """
    name_time_list = []
    with open(csv_path, 'r', encoding='utf8') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                continue  # ヘッダ行をスキップ
            filename = row[1]  # ファイル名(拡張子なし)
            end_time = convert_to_seconds(row[3])  # 終了時刻
            name_time_list.append((filename, end_time))

    return name_time_list


def get_video_path_str(file_name):
    """ 動画ファイルのパスを取得する関数

    :param: file_name: 動画ファイルの名前 """
    path = Path("data", file_name)
    full_path = path.resolve()
    print(full_path, full_path.exists())
    video_path = str(path)
    return video_path


def process(name_time_list, video_path, output_dir):
    """ 動画の分割処理を行う関数

    :param: name_time_list: 分割情報のリスト
    :param: video_path: 動画ファイルのパス
    :param: output_dir: 分割後のファイルを保存するディレクトリ """
    start_time = 0
    for i, (filename, end_time) in enumerate(name_time_list, start=1):
        output_filename = f"{output_dir}{filename}.mp4"
        subprocess.call(
            ['ffmpeg', '-y', '-i', video_path, '-ss', str(start_time), '-to', str(end_time), '-c', 'copy',
             output_filename])

        # 先頭フレームをPNG画像として保存
        output_image_filename = f"{output_dir}{filename}.png"
        subprocess.call(
            ['ffmpeg', '-y', '-i', output_filename, '-vframes', '1', '-q:v', '2', output_image_filename])

        start_time = end_time

    print("動画の分割が完了しました。")


# メイン処理
def main(file_name_prefix):
    """ メイン処理

    :param: file_name_prefix: ファイル名のプレフィックス """
    csv_path = Path(f"data/{file_name_prefix}.csv")  # CSVファイルのパス
    name_time_list = get_split_times(csv_path)  # 分割情報のリスト
    video_path = get_video_path_str(f"{file_name_prefix}.mp4")  # 動画ファイルのパス

    # 分割後のファイルを保存するディレクトリ
    output_dir = "data/results/"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    process(name_time_list, video_path, output_dir)


if __name__ == '__main__':
    # file_name_prefix はコマンドライン引数で指定
    if len(sys.argv) > 1:
        file_name_prefix = sys.argv[1]
    else:
        # data ディレクトリ内で見つけた .mp4 ファイルを対象にする
        file_name_prefix = next(Path("data").glob("*.mp4")).stem
    main(file_name_prefix)
