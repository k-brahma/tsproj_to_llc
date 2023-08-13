import os
import pathlib
import subprocess

import cv2


def extract_audio_and_merge(video_path, tmp_mp4_path, segment):
    """
    動画から音声を切り出し、別の動画と結合する

    :param video_path: video path, pathlib.Path
    :param tmp_mp4_path: ファイル名だがプロジェクトの tmp ディレクトリにあるものなので事実上パスと同じ
    :param segment:
    """
    start_time, end_time, output_name = segment.get("start", 0), segment["end"], segment["name"]

    tmp_audio_path = f"tmp/_{output_name}.aac"
    if os.path.exists(tmp_audio_path):
        os.remove(tmp_audio_path)

    subprocess.call([
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-ss", str(start_time),
        "-to", str(end_time),
        "-q:a", "0",
        "-map", "a",
        tmp_audio_path,
    ])

    output_video_path = video_path.parent / 'mp4' / f'{output_name}.mp4'
    if not output_video_path.parent.exists():
        os.makedirs(output_video_path.parent)
    if os.path.exists(output_video_path):
        os.remove(output_video_path)

    # 切り出した映像と音声を結合
    subprocess.call([
        "ffmpeg",
        "-y",
        "-i", tmp_mp4_path,
        "-i", tmp_audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-strict", "experimental",
        output_video_path,
    ])

    # 一時ファイルを削除
    os.remove(tmp_mp4_path)
    os.remove(tmp_audio_path)


def create_thumbnail_file(video_path, segment):
    """ デフォルトのサムネイルを生成"""
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
    """ デフォルトのサムネイルを生成"""
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


def cut_video_segments(config, create_thumbnail=True):
    """ 動画を切り出し、音声を割りつける """
    if not os.path.exists('tmp/'):
        os.makedirs('tmp/')

    mp4_dir = pathlib.Path(config["config_file_path"].parent)
    mp4_name = config["mp4_name"]
    video_path = pathlib.Path.joinpath(mp4_dir, mp4_name)
    if not os.path.exists(video_path):
        raise Exception("動画ファイルが見つかりませんでした。")

    # ビデオキャプチャオブジェクトを作成
    cap = cv2.VideoCapture(str(video_path))

    # フレームレートを取得
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # ビデオの保存設定を作成
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    for segment in config["cutSegments"]:
        start_frame = int(segment.get("start", 0) * fps)
        end_frame = int(segment["end"] * fps)

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        tmp_mp4_path = f"tmp/_{segment['name']}.mp4"
        out = cv2.VideoWriter(tmp_mp4_path, fourcc, fps, (width, height))

        for _ in range(end_frame - start_frame):
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
        out.release()

        # subprocess にて音声ファイルを切り出して割り当てる。また、サムネイルを作成する。
        extract_audio_and_merge(video_path, tmp_mp4_path, segment)
        if create_thumbnail:
            create_thumbnail_file(video_path, segment)

    cap.release()
    cv2.destroyAllWindows()
