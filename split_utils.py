import os
import pathlib
import subprocess
from concurrent.futures import ProcessPoolExecutor


def cut_video_segment(video_path, segment):
    start_time = segment.get("start", 0)
    end_time = segment["end"]
    output_name = segment["name"]

    output_video_path = pathlib.Path(video_path).parent / 'mp4' / f'{output_name}.mp4'
    if not output_video_path.parent.exists():
        os.makedirs(output_video_path.parent)

    # 動画と音声を同時に切り出す
    subprocess.call([
        "ffmpeg", "-i", video_path, "-ss", str(start_time), "-to", str(end_time),
        "-c", "copy", output_video_path
    ])


def cut_video_segments(config, create_thumbnail=True):
    config_file_path = config["config_file_path"]
    if isinstance(config_file_path, str):
        config_file_path = pathlib.Path(config_file_path)

    mp4_dir = pathlib.Path(config_file_path.parent)
    mp4_name = config["mp4_name"]
    video_path = pathlib.Path.joinpath(mp4_dir, mp4_name)
    if not os.path.exists(video_path):
        raise Exception("動画ファイルが見つかりませんでした。")

    with ProcessPoolExecutor() as executor:
        futures = []

        for segment in config["cutSegments"]:
            # タスクを非同期でスケジュール
            futures.append(executor.submit(cut_video_segment, str(video_path), segment))
            if create_thumbnail:
                futures.append(executor.submit(create_thumbnail_file, video_path, segment))

        # 全てのタスクが完了するのを待つ
        for future in futures:
            future.result()


def create_thumbnail_file(video_path, segment):
    """
    デフォルトのサムネイルを生成

    :param video_path: video path, pathlib.Path
    :param segment: 動画の切り出し箇所と生成するファイルのファイル名を含む辞書
    """
    file_name, millisecond = segment["name"], segment.get("thumbnail", 20000)

    mp4_path = video_path.parent / f'mp4/{file_name}.mp4'
    thumbnail_path = video_path.parent / f'mp4/{file_name}.png'
    subprocess.call([
        "ffmpeg",
        "-y",
        "-i", mp4_path,
        "-ss", str(int(millisecond / 1000)),
        "-vframes", "1",
        thumbnail_path
    ])


def create_thumbnail_files(config):
    """
    デフォルトのサムネイルを生成

    :param config: config file, dict
    """
    config_file_path = config["config_file_path"]
    if isinstance(config_file_path, str):
        config_file_path = pathlib.Path(config_file_path)
    mp4_dir = pathlib.Path(config_file_path.parent)
    mp4_name = config["mp4_name"]
    video_path = pathlib.Path.joinpath(mp4_dir, mp4_name)
    if not os.path.exists(video_path):
        raise Exception("動画ファイルが見つかりませんでした。")

    for segment in config["cutSegments"]:
        create_thumbnail_file(video_path, segment)
