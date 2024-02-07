import os
def checkInputFile(filepath):


    # ファイルが存在するか確認
    if os.path.exists(filepath):
        # ファイルの拡張子が ".mp4" か確認
        if filepath.lower().endswith('.mp4'):
            # ファイルサイズを取得（バイト単位）
            file_size = os.path.getsize(filepath)
            
            # ファイルサイズをGB単位に変換
            file_size_gb = file_size / (1024 ** 3)  # 1GB = 1024^3 bytes
            
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
