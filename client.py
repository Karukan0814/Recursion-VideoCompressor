import socket
import sys
import os
import json
import time

from lib import checkInputFile

# MMP プロトコル関連の定数
JSON_SIZE_BYTES = 16
PAYLOAD_SIZE_BYTES = 47
HEADER_SIZE = JSON_SIZE_BYTES + PAYLOAD_SIZE_BYTES


def request_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # サーバが待ち受けているポートにソケットを接続します
    server_address = "localhost"
    server_port = 9001

    print("connecting to {}:{}".format(server_address, server_port))

    try:
        # 接続後、サーバとクライアントが相互に読み書きができるようになります
        sock.connect((server_address, server_port))
    except socket.error as err:
        print(err)
        sys.exit(1)

    try:
        file_path = input("Type in a file to upload: ")
        # ファイルを送信する場合は、mp4ファイルで4GB以下に制限
        checkFileResult = checkInputFile(file_path)

        if not checkFileResult:
            raise Exception("File Error")

        # 動画ファイルをアップロード
        media_type = "mp4"  # 送信するメディアの種類
        mode = input(
            "何してほしいか。1:圧縮 2:解像度変更 3:アスペクト変更 4:音声変換 5:GIF作成 "
        )
        print("mode", mode)

        json_data = {"file_path": file_path, "media_type": media_type, "mode": mode}

        if mode == "2":
            # 解像度変更の場合、解像度を入力して送信
            resolution = input("解像度を入力してください (例: '640:360'): ")
            json_data["resolution"] = resolution
        elif mode == "3":
            # アスペクト比変更の場合、アスペクト比を入力して送信
            aspect_ratio = input("アスペクト比を入力してください (例: '16:9'): ")
            json_data["aspect_ratio"] = aspect_ratio
        elif mode == "5":
            # GIF作成の場合、フォーマット、開始時間、終了時間を入力して送信
            format = input("フォーマットを選択してください (gif または webm): ")
            json_data["format"] = format

            start_time = input("開始時間を入力してください (例: '00:00:10'): ")
            json_data["start_time"] = start_time

            end_time = input("終了時間を入力してください (例: '00:00:20'): ")
            json_data["end_time"] = end_time
        elif mode == "1" or mode == "4":
            pass
        else:
            print("無効なモードです")
            raise Exception("Invalid mode was selected")

        # バイナリモードでファイルを読み込む
        with open(file_path, "rb") as f:
            # ファイル名をペイロードに
            filename = os.path.basename(f.name)
            json_data["file_name"] = filename

            # JSON サイズ、メディアタイプ、ペイロードサイズを計算
            json_payload = json.dumps(json_data)
            json_payload_bytes = json_payload.encode("ISO-8859-1")

            json_size = len(json_payload_bytes)
            media_type = json_data["media_type"]
            payload_size = os.path.getsize(json_data["file_path"])
            print("json_string", json_payload)

            # ヘッダを作成
            header = json_size.to_bytes(JSON_SIZE_BYTES, byteorder="big")
            header += media_type.encode("utf-8")
            header += payload_size.to_bytes(PAYLOAD_SIZE_BYTES, byteorder="big")

            # ヘッダとペイロードを送信
            sock.sendall(header)

            # JSONデータを送信
            print("send_jsondata", json_payload_bytes)
            sock.send(json_payload_bytes)

            # ファイルを送信
            data = f.read(1400)
            while data:
                print("Sending...")
                sock.send(data)
                data = f.read(1400)

            # サーバーからファイルIDを受け取る
            file_id = sock.recv(1024).decode()  # サーバからのレスポンスを受け取る
            print("file_id", file_id)

            # ファイル送信後、一分ごとにファイルの状態をサーバに聞く
            # 聞いた結果が”完了”だったら処理終了
            # 処理中であればまた一分後にサーバーに状態を聞く

            ask_server(file_id)

    finally:
        print("closing socket")
        sock.close()


def ask_server(file_id: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # サーバが待ち受けているポートにソケットを接続します
    server_address = "localhost"
    server_port = 9002

    print("connecting to {}:{}".format(server_address, server_port))

    try:
        # 接続後、サーバとクライアントが相互に読み書きができるようになります
        sock.connect((server_address, server_port))
    except socket.error as err:
        print(err)
        sys.exit(1)
    try:
        while True:
            # ここでサーバに処理状態を問い合わせるリクエストを送る
            sock.sendall(file_id.encode())
            status = sock.recv(1024).decode()  # サーバからのレスポンスを受け取る
            print("status", status)
            if status == 2:
                # output_path = sock.recv(
                #     1024
                # ).decode()  # サーバからのレスポンスを受け取る

                # print(output_path)
                print("done!")
                break
            elif status == 999:
                print("該当のファイルは存在しません")
                break

            else:
                print("Processing... Waiting another minute.")
                time.sleep(60)  # 60秒待つ
                continue

    except Exception as e:
        print(f"Error: {e}")

    finally:
        print("Closing socket2.")
        sock.close()


def main():
    request_server()


main()
