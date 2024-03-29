import socket
import os
import json
import threading
import time

from pathlib import Path
from lib import (
    compress_video,
    change_resolution,
    change_aspect_ratio,
    convert_to_audio,
    create_gif_or_webm,
)


# このステージでは、ユーザーが動画ファイルをサーバにアップロードし、そのファイルに対して動画処理ができるサービスを開発します。処理が完了した動画ファイルはサーバからユーザーに返されます。サーバとクライアントは、TCP とカスタムアプリケーションレベルプロトコルを使って、さまざまな種類のファイルを互いに送信できるようにします。以下に、このサービスで提供される動画処理機能の一覧があります。


# 動画を圧縮する: ユーザーは動画ファイルをサーバにアップロードし、圧縮されたバージョンをダウンロードできます。サーバが自動的に最適な圧縮を選択します。
# 動画の解像度を変更する: ユーザーが動画をアップロードして希望する解像度を選択すると、その解像度に変更された動画がダウンロードできます。
# 動画のアスペクト比を変更する: ユーザーが動画をアップロードして希望するアスペクト比を選ぶと、そのアスペクト比に変更された動画がダウンロードできます。
# 動画を音声に変換する: 動画ファイルをアップロードすると、その動画から音声だけを抽出した MP3 バージョンがダウンロードできます。
# 指定した時間範囲で GIF や WEBM を作成: ユーザーが動画をアップロードし、時間範囲を指定すると、その部分を切り取って GIF または WEBM フォーマットに変換します。
# すべての動画処理は FFMPEG を使って行います。
# 受け付けたファイルの情報を保存するクラス
class File:
    def __init__(self, file_id: str, input_path: str, output_path: str, state=0):
        self.file_id = file_id  # 被らないようにタイムスタンプをidとして利
        self.state = state  # 0 はリクエスト、1 は処理中、2 は完了
        self.input_path = input_path
        self.output_path = output_path


# 受け付けたファイルのリスト
file_map: {str: File} = {}


def receive_request():

    # まず、必要なモジュールをインポートし、ソケットオブジェクトを作成して、アドレスファミリ（AF_INET）とソケットタイプ（SOCK_STREAM）を指定します。サーバのアドレスは、任意のIPアドレスからの接続を受け入れるアドレスである0.0.0.0に設定し、サーバのポートは9001に設定されています。
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = "0.0.0.0"
    server_port = 9001

    # MMP プロトコル関連の定数
    JSON_SIZE_BYTES = 16
    MEDIA_TYPE_BYTES = 1
    PAYLOAD_SIZE_BYTES = 47
    HEADER_SIZE = JSON_SIZE_BYTES + MEDIA_TYPE_BYTES + PAYLOAD_SIZE_BYTES

    # 次に、現在の作業ディレクトリに「temp」という名前のフォルダが存在するかどうかをチェックします。存在しない場合は、os.makedirs() 関数を使用してフォルダを作成します。このフォルダは、クライアントから受信したファイルを格納するために使用されます。
    input_path = "input"
    if not os.path.exists(input_path):
        os.makedirs(input_path)
    output_path = "output"
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    print("Starting up on {} port {}".format(server_address, server_port))

    # 次に、サーバは bind()関数を使用して、ソケットをサーバのアドレスとポートに紐付けします。その後、listen()関数を呼び出すことで、サーバは着信接続の待ち受けを開始します。サーバは一度に最大1つの接続を受け入れることができます。
    sock.bind((server_address, server_port))

    sock.listen(1)

    while True:
        # その後、サーバは無限ループに入り、クライアントからの着信接続を継続的に受け付けます。このコードでは、accept()関数を使用して、着信接続を受け入れ、クライアントのアドレスを取得します。
        connection, client_address = sock.accept()
        try:
            print("connection from", client_address)
            # 次に、クライアントから受信したデータのヘッダを読み取り、変数headerに格納します。ヘッダには、ファイル名の長さ、JSON データの長さ、クライアントから受信するデータの長さに関する情報が含まれています。
            header = connection.recv(HEADER_SIZE)

            # ヘッダから各種情報を抜き出す
            json_size = int.from_bytes(header[:JSON_SIZE_BYTES], byteorder="big")
            media_type = header[
                JSON_SIZE_BYTES : JSON_SIZE_BYTES + MEDIA_TYPE_BYTES
            ].decode()
            payload_size = int.from_bytes(header[-PAYLOAD_SIZE_BYTES:], byteorder="big")
            print("json_size", json_size)

            # JSONデータを受信
            data = b""
            while len(data) < json_size + 2:
                packet = connection.recv(json_size + 2 - len(data))
                if not packet:
                    break
                data += packet

            # data = connection.recv(json_size + 2)
            print("data", data)
            # バイト文字列をデコードしてUnicode文字列に変換
            unicode_string = data.decode("ISO-8859-1")
            print("unicode_string", unicode_string)

            # 'u\xd0' を削除して、残りの部分を取得
            cleaned_string = unicode_string.replace("u\xd0", "")
            print("cleaned_string", cleaned_string)

            json_payload = json.loads(cleaned_string)

            print("json_payload", json_payload)

            mode = json_payload["mode"]
            file_name = json_payload["file_name"]
            print("file_name", file_name)
            print("mode", mode)

            stream_rate = 1400

            # ファイルIDを作成し、ファイルリストマップに入れる
            # # ファイル名＋タイムスタンプ→intで一意なfile_idを作成する
            # # 現在のタイムスタンプを取得
            timestamp = str(time.time())
            # # ファイル名とタイムスタンプを結合
            file_id = file_name + timestamp
            print("file_id", file_id)

            # 生成したファイルIDをクライアント側に送る
            connection.sendall(file_id.encode())

            # # ファイルリストに入れる
            file_info = File(file_id, "", "")
            file_map[file_id] = file_info

            print("filemap", file_map)

            # ファイルを書き込む準備
            with open(os.path.join(input_path, file_name), "wb") as file:
                # ファイルの内容を受信し、ファイルに書き込む
                received_bytes = 0
                while received_bytes < payload_size:
                    data = connection.recv(stream_rate)
                    # print("data", data)
                    if not data:
                        break
                    file.write(data)
                    received_bytes += len(data)
                    # print("received_bytes", received_bytes)

            print("Finished downloading the file from client.")

            # クライアントからのinputファイルの保存パスを格納
            file_map[file_id].input_path = input_path + file_name
            file_map[file_id].state = 1
            print("state", file_map[file_id].state)

            # 以下、モードごとにinputfileを加工する
            output_file_path = ""
            if mode == "1":
                output_file_path = compress_video(file_name)
            elif mode == "2":
                resolution = json_payload["resolution"]
                output_file_path = change_resolution(file_name, resolution)
            elif mode == "3":
                aspect_ratio = json_payload["aspect_ratio"]
                output_file_path = change_aspect_ratio(file_name, aspect_ratio)
            elif mode == "4":
                output_file_path = convert_to_audio(file_name)
            elif mode == "5":
                format = json_payload["format"]

                start_time = json_payload["start_time"]
                end_time = json_payload["end_time"]
                output_file_path = create_gif_or_webm(
                    file_name, start_time, end_time, format
                )
            print("output_file_path", output_file_path)

            # 加工後のファイルの保存パスを格納
            file_map[file_id].output_path = output_file_path

            # 加工処理が終わったらファイルリストの該当ファイルの状態を変更
            file_map[file_id].state = 2
            print("state", file_map[file_id].state)

        except Exception as e:
            print("Error: " + str(e))

        finally:
            print("Closing current connection")
            connection.close()


def respond_file_state():
    # 現在処理中のファイル一覧の処理結果を確認

    # まず、必要なモジュールをインポートし、ソケットオブジェクトを作成して、アドレスファミリ（AF_INET）とソケットタイプ（SOCK_STREAM）を指定します。サーバのアドレスは、任意のIPアドレスからの接続を受け入れるアドレスである0.0.0.0に設定し、サーバのポートは9001に設定されています。
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = "0.0.0.0"
    server_port = 9002

    print("Starting up on {} port {}".format(server_address, server_port))

    # 次に、サーバは bind()関数を使用して、ソケットをサーバのアドレスとポートに紐付けします。その後、listen()関数を呼び出すことで、サーバは着信接続の待ち受けを開始します。サーバは一度に最大1つの接続を受け入れることができます。
    sock.bind((server_address, server_port))

    sock.listen(1)

    while True:
        # その後、サーバは無限ループに入り、クライアントからの着信接続を継続的に受け付けます。このコードでは、accept()関数を使用して、着信接続を受け入れ、クライアントのアドレスを取得します。
        connection, client_address = sock.accept()
        try:
            print("connection from", client_address)
            # クライアントが確認したいファイルのIDを取り出す
            file_id_byte = connection.recv(1024)
            file_id = file_id_byte.decode()
            print("check file_id", file_id)

            # 処理中のファイルリストから該当のファイルを取り出す
            if file_id in file_map:

                file_Info = file_map[file_id]
                state = file_Info.state
                print("file_id", file_id)
                print("state", state)

                if state == 0 or state == 1:
                    connection.sendall(state.to_bytes(1, "big"))

                elif state == 2:
                    connection.sendall(state.to_bytes(1, "big"))

                    output_path = file_Info.output_path
                    connection.sendall(output_path.encode("utf-8"))

                    # 処理中ファイルリストから削除する
                    removed_file = file_map.pop(file_id, None)
                    print(removed_file.file_id + "を処理が正常終了したため削除しました")

                else:
                    # 不正な値が入っているため処理中ファイルリストから削除する
                    removed_file = file_map.pop(file_id, None)
                    connection.sendall("異常終了".encode("utf-8"))

            else:
                # 該当のファイルがない場合
                state = 999
                connection.sendall(state.to_bytes(1, "big"))

        except Exception as e:
            print("Error: " + str(e))

        finally:
            print("Closing current connection")


def main():
    # 新規のファイル加工を受け付けるスレッド
    receive_request_thread = threading.Thread(target=receive_request)

    # 加工が終わったファイルの情報をクライアント側に投げるスレッド
    respond_thread = threading.Thread(target=respond_file_state)

    # スレッドを開始
    receive_request_thread.start()
    respond_thread.start()


main()
