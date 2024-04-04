""" パスと分割タイミングのリストを渡して直接動画を分割するプログラム

opencv 版（非同期処理 + 動画の複製） """
import asyncio
import shutil
import tempfile
from pathlib import Path

import cv2
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip


def convert_to_seconds(time_str):
    """ 文字列形式の時間（'HH:MM:SS'）を秒単位に変換する関数

    :param: time_str: 文字列形式の時間（'HH:MM:SS'）
    """
    hours, minutes, seconds = map(int, time_str.split(':'))
    return hours * 3600 + minutes * 60 + seconds


async def split_video(video_path, split_times, output_prefix):
    """ 動画を分割する非同期関数

    :param video_path: 入力動画のパス
    :param split_times: 分割タイミングのリスト（秒単位）
    :param output_prefix: 出力ファイル名のプレフィックス
    """
    # 動画を読み込む
    video = cv2.VideoCapture(video_path)

    # 動画の情報を取得
    fps = video.get(cv2.CAP_PROP_FPS)
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 現在の分割インデックス
    split_index = 0

    # 現在のフレーム番号
    current_frame = 0

    # 動画書き込み用のオブジェクト
    output = None

    while True:
        ret, frame = video.read()
        if not ret:
            break

        if current_frame == int(split_times[split_index] * fps):
            if output:
                output.release()

            output_filename = f"{output_prefix}{split_index + 1:02d}.mp4"
            print(output_filename)
            output = cv2.VideoWriter(output_filename, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
            split_index += 1

        if output:
            output.write(frame)

        current_frame += 1

    # 最後の分割ファイルを閉じる
    if output:
        output.release()

    # 動画を閉じる
    video.release()


async def process_video(video_path, split_times, output_prefix, temp_dir):
    """ 動画を処理する非同期関数

    :param video_path: 入力動画のパス
    :param split_times: 分割タイミングのリスト（秒単位）
    :param output_prefix: 出力ファイル名のプレフィックス
    :param temp_dir: 一時ディレクトリ
    """
    # 一時ファイルに動画を複製
    temp_video_path = Path(temp_dir) / "temp_video.mp4"
    shutil.copy(video_path, temp_video_path)

    # 動画を分割
    await split_video(str(temp_video_path), split_times, output_prefix)

    # 音声を抽出
    audio = AudioFileClip(str(temp_video_path))

    # 分割後の動画ファイルに音声を割り当て
    for i in range(len(split_times) - 1):
        output_filename = f"{output_prefix}{i + 1:02d}.mp4"
        start_time = split_times[i]
        end_time = split_times[i + 1]
        video_clip = VideoFileClip(output_filename)
        audio_clip = audio.subclip(start_time, end_time)
        video_clip = video_clip.set_duration(end_time - start_time)
        video_clip = video_clip.set_audio(CompositeAudioClip([audio_clip]))
        video_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')

    # 一時ファイルを削除
    temp_video_path.unlink()


# 文字列形式の分割タイミングのリスト
split_time_str_list = [
    "00:00:00",  # 最初の分割ポイントを追加
    "00:11:07",
    "00:30:32",
    "00:41:45",
    "00:44:06",
    "00:55:38",
    "01:07:58",
    "01:21:05",
    "01:37:21",
    "01:39:47",
    "01:46:28",
    "01:54:47",
]

# 秒単位の分割タイミングを算出
split_times = [convert_to_seconds(time_str) for time_str in split_time_str_list]

# 動画ファイルのパス
path = Path("data", "python_semianr_live_220731.mp4")

full_path = path.resolve()

print(full_path, full_path.exists())
video_path = str(path)

# 分割後のファイル名のプレフィックス
output_prefix = "data/opencv_async/python_semianr_live_220731_"

# 一時ディレクトリを作成
with tempfile.TemporaryDirectory() as temp_dir:
    # 動画処理の非同期タスクを作成
    video_tasks = []
    for i in range(len(split_times) - 1):
        task = asyncio.create_task(process_video(video_path, split_times[i:i + 2], output_prefix, temp_dir))
        video_tasks.append(task)

    # イベントループを作成し、非同期タスクを実行
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*video_tasks))

print("動画の分割が完了しました。")
