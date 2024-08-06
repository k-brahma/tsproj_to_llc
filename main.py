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
import argparse
import csv
import os.path
from pathlib import Path

from movie_processor import process_mp4_files


def get_split_info_list(csv_path):
    """ CSVファイルから分割タイミングを読み込む関数

    csv ファイルは以下の列を有する。
    ID,ファイル名,タイトル,終了時刻
    このうち、ファイル名と終了時刻を取得する。

    :param: csv_path: CSVファイルのパス

    :return: name_time_list: [(ファイル名, 終了時刻), ...]
    """
    name_time_list = []
    with open(csv_path, 'r', encoding='utf8') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                continue  # ヘッダ行をスキップ

            filename = row[1]  # ファイル名(拡張子なし)

            # 文字列形式の時間（'HH:MM:SS'）を秒単位に変換する
            hours, minutes, seconds = map(int, row[3].split(':'))
            end_time = hours * 3600 + minutes * 60 + seconds  # 終了時刻

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


def main():
    """ 動画を分割してサムネイルを生成するプログラム。

    params:
        - `file_name_prefix` (optional): 動画ファイルのプレフィックス。CSVファイルについても同じ名前を持つ必要があります。
        - `--no-thumbnails` または `-n`: サムネイルを生成しないフラグ
        - `--thumbnail-interval` または `-i`: サムネイル生成の間隔（秒）

    output:
        - 分割された動画ファイルは `data/results/` ディレクトリに保存されます。

    usage:
        以下のようにコマンドラインから実行します:
        python main.py [file_name_prefix] --no-thumbnails --thumbnail-interval [interval]

        例えば、`example_video.mp4` という 動画ファイルが `data/` ディレクトリ内に存在する場合:
        以下のコマンドは `example_video.mp4` を分割し、5秒ごとにサムネイルを生成せずに `data/results/` に保存します。
            python main.py example_video --no-thumbnails --thumbnail-interval 5
    """
    parser = argparse.ArgumentParser(description='動画分割プログラム。')
    parser.add_argument('file_name_prefix',
                        help='ファイル名のプレフィックス。省略した場合は data dir 内の mp4 ファイルを見つけて使用します。')
    parser.add_argument('--thumbnail-interval', '-i', type=int, default=0,
                        help='サムネイル候補生成の秒間隔。0の場合サムネイルを生成しません。')
    args = parser.parse_args()

    file_name_prefix = args.file_name_prefix
    video_path = get_video_path_str(f"{file_name_prefix}.mp4")  # 動画ファイルのパス
    csv_path = Path(f"data/{file_name_prefix}.csv")  # CSVファイルのパス
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"動画ファイルが見つかりませんでした: {video_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSVファイルが見つかりませんでした: {csv_path}")

    split_info_list = get_split_info_list(csv_path)

    # 分割後のファイルを保存するディレクトリ
    output_dir = "data/results/"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    process_mp4_files(
        split_info_list, video_path, output_dir,
        thumbnail_interval=args.thumbnail_interval,
        max_workers=4
    )


if __name__ == '__main__':
    main()
