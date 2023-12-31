"""
regex pattern p[0-9]+_.*+ にマッチするネーミングルールで付与されたタグをもとに、動画を分割する
"""
import json
import pathlib
import re


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

            # get regex pattern p[0-9]+_.*+
            match = re.match(r'^p_(\d{2})_', name)
            if match:
                num = int(match.group(1))
            else:
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
    LossLessCut 用の .llc ファイルを作成する

    :param opencv_dict: oepcv 用の dict
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
