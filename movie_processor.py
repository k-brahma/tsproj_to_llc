import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2


def generate_thumbnails_by_opencv(output_dir, filename, output_mp4_name, thumbnail_interval, overwrite_thumbnails):
    """ 動画からサムネイルを生成する関数, OpenCVを使用

    :param output_dir: 出力ディレクトリ
    :param filename: ファイル名
    :param output_mp4_name: 出力動画ファイル名
    :param thumbnail_interval: サムネイル生成の間隔（秒） 0 の場合はサムネイルを生成しない
    :param overwrite_thumbnails: 既存のものがある場合に上書きするかどうか
    """
    if thumbnail_interval == 0:
        return

    # サムネイルを保存するディレクトリを作成
    output_sub_dir = Path(f"{output_dir}{filename}")
    output_sub_dir.mkdir(parents=True, exist_ok=True)

    # 動画ファイルを読み込み、基本情報を収集
    cap = cv2.VideoCapture(output_mp4_name)  # VideoCaptureクラスのインスタンスを生成
    fps = cap.get(cv2.CAP_PROP_FPS)  # 1秒あたりのフレーム数を取得
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 動画の総フレーム数を取得

    n = len(str(total_frames))  # total_framesの桁数を取得
    for i in range(0, total_frames // int(fps * thumbnail_interval) + 2):
        frame_num = i * int(fps * thumbnail_interval)
        output_path = output_sub_dir / f"{filename}_{frame_num:0{n}d}.png"
        if overwrite_thumbnails or not os.path.exists(output_path):
            frame_num = (i - 1) * int(fps * thumbnail_interval)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(str(output_path), frame)

    cap.release()


def split_video(base_video_path, output_file_name, start_time, end_time):
    """ 動画分割処理を行う関数 """
    subprocess.call(
        [
            'ffmpeg',
            '-y',  # overwrite output file if it exists
            '-i', base_video_path,  # input file
            '-ss', str(start_time),  # start time
            '-to', str(end_time),  # end time
            '-c', 'copy',  # copy codec. -c でコーデックを指定する。copy で入力ファイルと同じコーデックを使用する。
            output_file_name,  # output file
        ]
    )


def process_single_video(filename, end_time, base_video_path, output_dir, start_time, thumbnail_interval,
                         overwrite_thumbnails):
    """ 単一の動画に対する分割とサムネイル生成を行う関数

    :param filename: ファイル名
    :param end_time: 終了時刻
    :param base_video_path: 基本動画ファイルのパス
    :param output_dir: 出力ディレクトリ
    :param start_time: 開始時刻
    :param thumbnail_interval: サムネイル生成の間隔（秒）
    """
    output_file_name = f"{output_dir}{filename}.mp4"

    # 動画の分割
    split_video(base_video_path, output_file_name, start_time, end_time)

    # 分割した動画を読み込んでの thumbnails 生成
    generate_thumbnails_by_opencv(output_dir, filename, output_file_name, thumbnail_interval, overwrite_thumbnails)


def process_mp4_files(name_time_list, base_video_path, output_dir, thumbnail_interval, overwrite_thumbnails,
                      max_workers):
    """ メイン処理を行う関数

    :param name_time_list: [(ファイル名, 終了時刻), ...]
    :param base_video_path: 動画ファイルのパス
    :param output_dir: 出力ディレクトリ
    :param thumbnail_interval: サムネイル生成の間隔（秒）
    :param overwrite_thumbnails: 既存のサムネイルを上書きするかどうか
    :param max_workers: 最大ワーカー数
    """
    start_time = time.monotonic()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        srate_time = 0
        for filename, end_time in name_time_list:
            future = executor.submit(
                process_single_video,
                filename, end_time, base_video_path, output_dir, srate_time, thumbnail_interval, overwrite_thumbnails
            )
            futures.append(future)
            srate_time = end_time

        # すべてのタスクが完了するのを待つ
        for future in futures:
            future.result()

    end_time = time.monotonic()
    total_time = end_time - start_time  # 総所要時間を計算

    print(f"すべての処理が完了しました。総所要時間: {total_time:.2f}秒")
