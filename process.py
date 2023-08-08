import json
import pathlib


def process(file_path):
    result_list = []
    path = pathlib.Path(file_path)

    # open file as json
    with path.open(encoding='utf8') as f:
        data = json.load(f)
        timeline = data['timeline']
        parameters = timeline['parameters']
        toc = parameters['toc']
        keyframes = toc['keyframes']

        start = None
        for keyframe in keyframes:
            name = keyframe['value']

            # check tag name
            spl = name.split('_')
            if len(spl) == 1:
                continue
            if spl[0].isdigit() is False:
                continue

            end = keyframe['time'] / 706000000
            result_list.append((start, end, name))
            start = end

    # create new dict
    new_dict = {
        'version': 1,
        'mediaFileName': 'support_230805_base.mp4',
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

        new_dict['cutSegments'].append(temp_dict)

    # create js object
    # Convert to JSON
    json_str = json.dumps(new_dict, indent=2, ensure_ascii=False)

    # Make it look like a JS object by removing double quotes around keys
    js_object_str = '\n'.join(
        line.replace('\"', '') if line.strip().endswith(':') else line for line in json_str.splitlines()
    )

    output_path = path.parent / (path.stem + '.llc')

    # write to file
    with output_path.open('w', encoding='utf8') as f:
        f.write(js_object_str)
