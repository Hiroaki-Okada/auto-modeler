import pdb

import os
import shutil


def delete_directories_starting_with_x1():
    # 現在のディレクトリを取得
    current_directory = os.getcwd()

    # 1つ上のディレクトリに移動
    parent_directory = os.path.dirname(current_directory)
    os.chdir(parent_directory)

    # ディレクトリ内のすべてのファイルとディレクトリを取得
    all_files_and_directories = os.listdir()

    # X1から始まるディレクトリを見つけて削除
    for name in all_files_and_directories:
        if os.path.isdir(name) and name.startswith("X1-"):
            target_directory = os.path.join(parent_directory, name)
            try:
                # ディレクトリを削除
                shutil.rmtree(target_directory)
                print(f"削除されました: {target_directory}")
            except OSError as e:
                print(f"削除エラー: {e}")


if __name__ == "__main__":
    delete_directories_starting_with_x1()