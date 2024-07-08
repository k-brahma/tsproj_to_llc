from pathlib import Path

import cv2


def generate_thumbnails_in_memory(output_dir, filename, output_mp4_name, thumbnail_interval):
    """ 動画からサムネイルを生成する関数, OpenCVを使用 """
    output_sub_dir = Path(f"{output_dir}{filename}")
    output_sub_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(output_mp4_name)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for frame_num in range(0, total_frames, int(fps * thumbnail_interval)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if ret:
            output_path = output_sub_dir / f"{filename}_{frame_num // int(fps * thumbnail_interval) + 1:04d}.png"
            cv2.imwrite(str(output_path), frame)

    cap.release()
