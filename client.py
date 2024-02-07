import socket
import sys
import os

from lib import checkInputFile


# クライアントがサーバに接続し、mp4 ファイルをアップロードするためのサービスを開発します。サーバはバックグラウンドで動作し、クライアントは CLI を通じてサーバに接続します。クライアントが CLI でコマンドを実行すると、アップロードするファイルが選択されます。ファイルのアップロードが完了したら、サーバから状態を報告するメッセージがクライアントに送られます。

# 機能要件

#     サーバは CLI で起動し、バックグラウンドで着信接続を待機します。サーバが停止していると、それはサービスが停止しているという意味です。
#     クライアントは TCP を使用してサーバにファイルを送信する必要があります。TCP は UDP よりもオーバーヘッドが大きいですが、確実にファイル全体が送信されることを保証するためです。
#     TCP での送信では、比較的安定したパケットサイズを使ってください。TCP プロトコルに基づいて、パケットの上限サイズは 65535 バイト（16 ビット長）である可能性がありますが、通常の最大セグメントサイズは下位ネットワークレベルで 1460 バイトです。すべてのデータが送信されるまで、最大サイズとして 1400 バイトのパケットを使用してください。
#     接続プロトコルは基本的なものです。最初にサーバに送信される 32 バイトは、ファイルのバイト数をサーバに通知します。このプロトコルは最大で 4GB（232バイト）までのファイルに対応しています。
#     サーバは、受け取ったデータバイトを常に mp4 ファイルとして解釈します。他のファイル形式はサポートされていませんので、クライアントは送信するファイルが mp4 であることを確認する必要があります。
#     サーバは、レスポンスプロトコルを用いて応答します。これは、ステータス情報を含む 16 バイトのメッセージです。




sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# サーバが待ち受けているポートにソケットを接続します
server_address = "0.0.0.0"
server_port = 9001

print('connecting to {}'.format(server_address, server_port))

try:
    # 接続後、サーバとクライアントが相互に読み書きができるようになります 
    sock.connect((server_address, server_port))
except socket.error as err:
    print(err)
    sys.exit(1)

try:
    filepath = input('Type in a file to upload: ')
    # ファイルを送信する場合は、mp4ファイルで4GB以下に制限
    checkFileResult=checkInputFile(filepath)


    
    if checkInputFile==False:
        raise Exception("File Error")
    

    # バイナリモードでファイルを読み込む
    with open(filepath, 'rb') as f:
        


        filename = os.path.basename(f.name)

        # ファイル名からビット数
        filename_bits = filename.encode('utf-8')

        # ファイルサイズを取得（バイト単位）
        file_size = os.path.getsize(filepath)

        header = file_size.to_bytes(8,"big")

        # ヘッダの送信
        sock.send(header)

        # # ファイル名の送信
        # sock.send(filename_bits)

        data = f.read(1400)
        while data:
            print("Sending...")
            sock.send(data)
            data = f.read(1400)

finally:
    print('closing socket')
    sock.close()
