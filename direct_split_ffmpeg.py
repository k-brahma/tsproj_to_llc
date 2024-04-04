""" パスと分割タイミングのリストを渡して直接動画を分割するプログラム

ffmpeg 版
"""
import subprocess
from pathlib import Path


def convert_to_seconds(time_str):
    """ 文字列形式の時間（'HH:MM:SS'）を秒単位に変換する関数

    :param: time_str: 文字列形式の時間（'HH:MM:SS'）
    """
    hours, minutes, seconds = map(int, time_str.split(':'))
    return hours * 3600 + minutes * 60 + seconds


# 文字列形式の分割タイ21ミングのリスト
split_time_str_list = [
    "00:11:07",  # end of01
    "00:30:32",  # end of02
    # "00:41:16",  # end of03
    "00:44:05",  # end of03
    "00:55:38",  # end of04
    "01:06:58",  # end of05
    "01:21:05",  # end of06
    "01:37:21",  # end of07
    "01:39:47",  # end of08
    "01:46:28",  # end of09
    "01:54:47",  # end of10
]

# 秒単位の分割タイミングを算出
split_times = [convert_to_seconds(time_str) for time_str in split_time_str_list]

# 動画ファイルのパス
path = Path("data", "python_semianr_live_220731.mp4")

full_path = path.resolve()

print(full_path, full_path.exists())
video_path = str(path)

# 分割後のファイル名のプレフィックス
output_prefix = "data/ffmpeg/python_semianr_live_220731_"

# 分割タイミングのペアを作成
split_pairs = [(0, split_times[0])] + list(zip(split_times, split_times[1:]))

# 動画を分割
for i, (start_time, end_time) in enumerate(split_pairs, start=1):
    output_filename = f"{output_prefix}{i:02d}.mp4"
    subprocess.call(
        ['ffmpeg', '-y', '-i', video_path, '-ss', str(start_time), '-to', str(end_time), '-c', 'copy', output_filename])

    # 先頭フレームをPNG画像として保存
    output_image_filename = f"{output_prefix}{i:02d}.png"
    subprocess.call(
        ['ffmpeg', '-y', '-i', output_filename, '-vframes', '1', '-q:v', '2', output_image_filename])

print("動画の分割が完了しました。")
