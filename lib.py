import os


def checkInputFile(filepath):

    # ファイルが存在するか確認
    if os.path.exists(filepath):
        # ファイルの拡張子が ".mp4" か確認
        if filepath.lower().endswith(".mp4"):
            # ファイルサイズを取得（バイト単位）
            file_size = os.path.getsize(filepath)

            # ファイルサイズをGB単位に変換
            file_size_gb = file_size / (1024**3)  # 1GB = 1024^3 bytes

            # ファイルサイズが4GB未満か確認
            if file_size_gb < 4:
                print("The file is an MP4 file and its size is under 4GB.")
                return True
            else:
                print("The file is an MP4 file but its size exceeds 4GB.")
                return False
        else:
            print("The file is not an MP4 file.")
            return False
    else:
        print("The file does not exist.")
        return False


import subprocess

input_folder = "input"
output_folder = "output"


def compress_video(input_file_name):

    # (1)動画を圧縮する: ユーザーは動画ファイルをサーバにアップロードし、圧縮されたバージョンをダウンロードできます。サーバが自動的に最適な圧縮を選択します。
    input_file_path = os.path.join(input_folder, input_file_name)
    output_file_path = os.path.join(output_folder, "output_1_" + input_file_name)

    command = [
        "ffmpeg",
        "-i",
        input_file_path,
        "-vf",
        "scale=640:360",
        "-c:a",
        "copy",
        output_file_path,
    ]
    subprocess.run(command, check=True)
    return output_file_path


def change_resolution(input_file_name, resolution):
    # (2)動画の解像度を変更する: ユーザーが動画をアップロードして希望する解像度を選択すると、その解像度に変更された動画がダウンロードできます。

    input_file_path = os.path.join(input_folder, input_file_name)
    output_file_path = os.path.join(output_folder, "output_2_" + input_file_name)

    command = [
        "ffmpeg",
        "-i",
        input_file_path,
        "-vf",
        "scale={}".format(resolution),
        "-c:a",
        "copy",
        output_file_path,
    ]
    subprocess.run(command, check=True)
    return output_file_path


def change_aspect_ratio(input_file_name, aspect_ratio):
    # (3)動画のアスペクト比を変更する: ユーザーが動画をアップロードして希望するアスペクト比を選ぶと、そのアスペクト比に変更された動画がダウンロードできます。
    input_file_path = os.path.join(input_folder, input_file_name)
    output_file_path = os.path.join(output_folder, "output_3_" + input_file_name)

    command = [
        "ffmpeg",
        "-i",
        input_file_path,
        "-vf",
        "setdar={}".format(aspect_ratio),
        "-c:a",
        "copy",
        output_file_path,
    ]
    subprocess.run(command, check=True)
    return output_file_path


def convert_to_audio(input_file_name):
    # (4)動画を音声に変換する: 動画ファイルをアップロードすると、その動画から音声だけを抽出した MP3 バージョンがダウンロードできます。
    input_file_path = os.path.join(input_folder, input_file_name)
    output_file_path = os.path.join(output_folder, "output_4_" + input_file_name)

    command = [
        "ffmpeg",
        "-i",
        input_file_path,
        "-vn",
        "-acodec",
        "libmp3lame",
        output_file_path,
    ]
    subprocess.run(command, check=True)
    return output_file_path


def create_gif_or_webm(input_file_name, start_time, end_time, format):
    # (5)指定した時間範囲で GIF や WEBM を作成: ユーザーが動画をアップロードし、時間範囲を指定すると、その部分を切り取って GIF または WEBM フォーマットに変換します。
    input_file_path = os.path.join(input_folder, input_file_name)
    output_file_path = os.path.join(output_folder, "output_5_" + input_file_name)

    command = [
        "ffmpeg",
        "-i",
        input_file_path,
        "-ss",
        start_time,
        "-to",
        end_time,
        output_file_path,
    ]
    if format == "gif":
        command += ["-vf", "fps=10", "-f", "gif"]
    elif format == "webm":
        command += ["-c:v", "libvpx", "-crf", "10", "-b:v", "1M", "-c:a", "libvorbis"]
    subprocess.run(command, check=True)
    return output_file_path
