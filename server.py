import socket
import os
from pathlib import Path

# まず、必要なモジュールをインポートし、ソケットオブジェクトを作成して、アドレスファミリ（AF_INET）とソケットタイプ（SOCK_STREAM）を指定します。サーバのアドレスは、任意のIPアドレスからの接続を受け入れるアドレスである0.0.0.0に設定し、サーバのポートは9001に設定されています。
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = "0.0.0.0"
server_port = 9001

# 次に、現在の作業ディレクトリに「temp」という名前のフォルダが存在するかどうかをチェックします。存在しない場合は、os.makedirs() 関数を使用してフォルダを作成します。このフォルダは、クライアントから受信したファイルを格納するために使用されます。
dpath = "temp"
if not os.path.exists(dpath):
    os.makedirs(dpath)

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
        # header = connection.recv(8)

        # ファイルのバイト数を受信
        filesize_bytes = connection.recv(4)
        filesize = int.from_bytes(filesize_bytes, byteorder="big")

        # ファイル名を受信
        filename = connection.recv(1024).decode()

        print("Filename: {}".format(filename))

        stream_rate = 1400

        # 次に、コードはクライアントから受け取ったファイル名で新しいファイルをtempフォルダに作成します。このファイルは、withステートメントを使用してバイナリモードで開かれ、write()関数を使用して、クライアントから受信したデータをファイルに書き込みます。データはrecv()関数を使用して塊単位で読み込まれ、データの塊を受信するたびにデータ長がデクリメントされます。
        # w+は終了しない場合はファイルを作成し、そうでない場合はデータを切り捨てます
        # with open(os.path.join(dpath, filename), "wb+") as f:

        # ファイルを書き込む準備
        with open(os.path.join(dpath, filename), "wb") as file:
            # ファイルの内容を受信し、ファイルに書き込む
            received_bytes = 0
            while received_bytes < filesize:
                data = connection.recv(stream_rate)
                if not data:
                    break
                file.write(data)
                received_bytes += len(data)

        print("Finished downloading the file from client.")

    except Exception as e:
        print("Error: " + str(e))

    finally:
        print("Closing current connection")
        connection.close()
