"""
動画分割プログラム（ffmpeg版）

このモジュールは、指定された動画ファイルをCSVファイルに基づいて複数のセグメントに分割します。
各セグメントの先頭フレームをPNG画像として保存する機能も含まれています。

主な機能:
1. CSVファイルから分割情報を読み込む
2. 動画ファイルを指定されたタイミングで分割する
3. 分割されたセグメントの先頭フレームをPNG画像として保存する

使用方法:
1. 'data'ディレクトリに分割したい.mp4ファイルを配置する
2. 同じ'data'ディレクトリに、分割情報を含むCSVファイルを配置する
3. コマンドラインから以下のように実行する:
   python split_video.py [file_name_prefix]

   [file_name_prefix]は任意。指定しない場合、'data'ディレクトリ内の最初の.mp4ファイルが使用される

CSVファイル形式:
CSVファイルは以下のフィールドを含む必要があります：
1. ID: セグメントの一意の識別子（例: 1, 2, 3...）
2. ファイル名: 分割後のセグメントのファイル名（拡張子なし）
3. タイトル: セグメントの説明的なタイトル（現在のコードでは使用されていない）
4. 終了時刻: セグメントの終了時間（HH:MM:SS形式）

CSVファイルの例:
ID,ファイル名,タイトル,終了時刻
1,intro,イントロダクション,00:02:30
2,main_part_1,主要な議論 パート1,00:15:45
3,main_part_2,主要な議論 パート2,00:30:20
4,conclusion,結論,00:35:00

注意:
- 各行は1つのセグメントに対応する
- 最初の行はヘッダーとして扱われ、スキップされる
- 終了時刻は累積時間。各セグメントの開始時間は前のセグメントの終了時間

必要条件:
- Python 3.x
- ffmpeg（システムにインストールされ、パスが通っていること）

出力:
- 分割された動画ファイル: 'data/results/'ディレクトリに保存
- セグメントの先頭フレーム画像: 同じく'data/results/'ディレクトリにPNG形式で保存

注意:
- 動画ファイルとCSVファイルの名前（拡張子を除く）は一致している必要がある
- ffmpegがインストールされていない場合、このスクリプトは動作しない

作者: [あなたの名前]
バージョン: 1.0
最終更新日: [更新日]
"""
import csv
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from thumbnail import generate_thumbnails_in_memory


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


def split_video(base_video_path, output_mp4_name, start_time, end_time):
    """ 単一の動画分割処理を行う関数 """
    subprocess.call(
        ['ffmpeg', '-y', '-i', base_video_path, '-ss', str(start_time), '-to', str(end_time), '-c', 'copy',
         output_mp4_name])


def create_thumbnail(video_path, output_path, time):
    """ 単一のサムネイルを生成する関数 """
    subprocess.call(
        ['ffmpeg', '-y', '-i', video_path, '-ss', str(time), '-vframes', '1', '-q:v', '2', str(output_path)])


import argparse


def process(name_time_list, base_video_path, output_dir, create_thumbnails=True, thumbnail_interval=10, max_workers=4):
    """ メイン処理を行う関数 """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        start_time = 0
        futures = []
        for filename, end_time in name_time_list:
            future = executor.submit(process_single_video, filename, end_time, base_video_path, output_dir, start_time,
                                     thumbnail_interval if create_thumbnails else None)
            futures.append(future)
            start_time = end_time

        # すべてのタスクが完了するのを待つ
        for future in futures:
            future.result()

    print("すべての処理が完了しました。")


def process_single_video(filename, end_time, base_video_path, output_dir, start_time, thumbnail_interval):
    """ 単一の動画に対する分割とサムネイル生成を行う関数 """
    output_mp4_name = f"{output_dir}{filename}.mp4"

    # 動画の分割
    split_video(base_video_path, output_mp4_name, start_time, end_time)

    # 分割した動画を読み込んでの thumbnails 生成
    # generate_thumbnails(output_dir, filename, output_mp4_name, thumbnail_interval)
    generate_thumbnails_in_memory(output_dir, filename, output_mp4_name, thumbnail_interval)


def generate_thumbnails(output_dir, filename, output_mp4_name, thumbnail_interval):
    """ ffmpeg を使った thumbnail の生成 """
    if thumbnail_interval is not None:
        output_sub_dir = Path(f"{output_dir}{filename}")
        output_sub_dir.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
             output_mp4_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        duration = float(result.stdout)

        thumbnail_times = list(range(0, int(duration), thumbnail_interval))
        thumbnail_paths = [output_sub_dir / f"{filename}_{i // thumbnail_interval + 1:04d}.png" for i in
                           thumbnail_times]

        for time, path in zip(thumbnail_times, thumbnail_paths):
            create_thumbnail(output_mp4_name, path, time)


def main():
    parser = argparse.ArgumentParser(description='動画分割プログラム')
    parser.add_argument('file_name_prefix', nargs='?', help='ファイル名のプレフィックス')
    parser.add_argument('--no-thumbnails', '-nt', action='store_true', help='サムネイルを生成しない')
    parser.add_argument('--thumbnail-interval', '-i', type=int, default=10, help='サムネイル生成の間隔（秒）')
    args = parser.parse_args()

    file_name_prefix = args.file_name_prefix
    if not file_name_prefix:
        # data ディレクトリ内で見つけた .mp4 ファイルを対象にする
        file_name_prefix = next(Path("data").glob("*.mp4")).stem

    csv_path = Path(f"data/{file_name_prefix}.csv")  # CSVファイルのパス
    name_time_list = get_split_times(csv_path)  # 分割情報のリスト
    video_path = get_video_path_str(f"{file_name_prefix}.mp4")  # 動画ファイルのパス

    # 分割後のファイルを保存するディレクトリ
    output_dir = "data/results/"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    process(name_time_list, video_path, output_dir,
            create_thumbnails=not args.no_thumbnails,
            thumbnail_interval=args.thumbnail_interval)


if __name__ == '__main__':
    main()
