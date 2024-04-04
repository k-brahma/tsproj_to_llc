""" パスと分割タイミングのリストを渡して直接動画を分割するプログラム

opencv 版（マルチプロセス） """
import cv2
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from multiprocessing import Process, Queue


def convert_to_seconds(time_str):
    """ 文字列形式の時間（'HH:MM:SS'）を秒単位に変換する関数

    :param: time_str: 文字列形式の時間（'HH:MM:SS'）
    """
    hours, minutes, seconds = map(int, time_str.split(':'))
    return hours * 3600 + minutes * 60 + seconds


def assign_audio(output_filename, start_time, end_time, audio):
    """ 動画ファイルに音声を割り当てる関数

    :param output_filename: 出力ファイル名
    :param start_time: 開始時間（秒）
    :param end_time: 終了時間（秒）
    :param audio: 音声クリップ
    """
    video_clip = VideoFileClip(output_filename)
    audio_clip = audio.subclip(start_time, end_time)
    video_clip = video_clip.set_duration(end_time - start_time)
    video_clip = video_clip.set_audio(CompositeAudioClip([audio_clip]))
    video_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')


def process_audio_assignment(audio_queue):
    """ 音声割り当てプロセスの関数

    :param audio_queue: 音声割り当ての情報を格納するキュー
    """
    while True:
        item = audio_queue.get()
        if item is None:
            break
        output_filename, start_time, end_time, audio = item
        assign_audio(output_filename, start_time, end_time, audio)


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

# 動画を読み込む
video = cv2.VideoCapture(video_path)

# 動画の情報を取得
fps = video.get(cv2.CAP_PROP_FPS)
width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 動画の長さを取得
frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

# 分割後のファイル名のプレフィックス
output_prefix = "data/opencv/python_semianr_live_220731_"

# 現在の分割インデックス
split_index = 0  # インデックスを0から開始

# 現在のフレーム番号
current_frame = 0

# 動画書き込み用のオブジェクト
output = None

# 音声を抽出
audio = AudioFileClip(video_path)

# 音声割り当ての情報を格納するキュー
audio_queue = Queue()

# 音声割り当てプロセスを作成
audio_process = Process(target=process_audio_assignment, args=(audio_queue,))
audio_process.start()

while True:
    ret, frame = video.read()
    if not ret:
        break

    if current_frame == int(split_times[split_index] * fps):
        if output:
            output.release()

            # 直前の分割ファイルの音声割り当て情報をキューに追加
            if split_index > 0:
                prev_output_filename = f"{output_prefix}{split_index:02d}.mp4"
                prev_start_time = split_times[split_index - 1]
                prev_end_time = split_times[split_index]
                audio_queue.put((prev_output_filename, prev_start_time, prev_end_time, audio))

        output_filename = f"{output_prefix}{split_index+1:02d}.mp4"
        print(output_filename)
        output = cv2.VideoWriter(output_filename, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
        split_index += 1

    if output:
        output.write(frame)

    current_frame += 1

# 最後の分割ファイルを閉じる
if output:
    output.release()

    # 最後の分割ファイルの音声割り当て情報をキューに追加
    last_output_filename = f"{output_prefix}{split_index:02d}.mp4"
    last_start_time = split_times[split_index - 1]
    last_end_time = audio.duration
    audio_queue.put((last_output_filename, last_start_time, last_end_time, audio))

# 動画を閉じる
video.release()

# 音声割り当てプロセスの終了を示すためにNoneをキューに追加
audio_queue.put(None)

# 音声割り当てプロセスの終了を待機
audio_process.join()

print("動画の分割が完了しました。")