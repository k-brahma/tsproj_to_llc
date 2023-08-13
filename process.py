import json
import pathlib

from split_utils import cut_video_segments, create_thumbnail_files


def create_opencv_config(file_path):
    """ opencv 用の dict を作成する """
    config_file_path = pathlib.Path(file_path)
    result_list = []
    with config_file_path.open(encoding='utf8') as f:
        data = json.load(f)
        mp4_name = data['sourceBin'][0]['src']

        _timeline = data['timeline']
        _parameters = _timeline['parameters']
        _toc = _parameters['toc']
        _keyframes = _toc['keyframes']

        start = None
        for keyframe in _keyframes:
            name = keyframe['value']

            # check tag name
            _spl = name.split('_')
            if len(_spl) == 1:
                continue
            if _spl[0].isdigit() is False:
                continue

            end = keyframe['time'] / 706000000
            result_list.append((start, end, name))
            start = end

    # create new dict
    result_dict = {
        'config_file_path': config_file_path,
        'mp4_name': mp4_name,
        'cutSegments': []
    }
    for start, end, name in result_list:
        temp_dict = {}
        if start is not None:
            temp_dict['start'] = start
        if end is not None:
            temp_dict['end'] = end
        if name is not None:
            temp_dict['name'] = name
        temp_dict['thumbnail'] = 20000

        result_dict['cutSegments'].append(temp_dict)

    output_path = config_file_path.parent / (config_file_path.stem + '_opencv.json')
    with output_path.open('w', encoding='utf8') as f:
        _dict = result_dict.copy()
        _dict['config_file_path'] = str(_dict['config_file_path'])
        f.write(json.dumps(_dict, indent=2, ensure_ascii=False))

    return result_dict


def create_llc_config(opencv_dict):
    """
    llc ファイルを作成する

    :param opencv_dict:
    :return: None
    """
    llc_dict = {
        'version': 1,
        'mediaFileName': opencv_dict['mp4_name'],
        'cutSegments': opencv_dict['cutSegments']
    }
    json_str = json.dumps(llc_dict, indent=2, ensure_ascii=False)
    js_object_str = '\n'.join(
        line.replace('\"', '') if line.strip().endswith(':') else line for line in json_str.splitlines()
    )

    config_file_path = pathlib.Path(opencv_dict['config_file_path'])
    output_path = config_file_path.parent / (config_file_path.stem + '.llc')
    with output_path.open('w', encoding='utf8') as f:
        f.write(js_object_str)


def process(file_path, create_llc=True, create_movie=False, create_thumbnail=False):
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
