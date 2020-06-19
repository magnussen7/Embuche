#!/usr/bin/python3.8
# coding: utf-8
import argparse
import os
import shutil
import glob

if __name__ == "__main__":
    dir_list = ['bin', 'build', 'src']
    parser = argparse.ArgumentParser(description='Little helper to create the structure of a new C projet.')
    parser.add_argument('path', type=str, help='Path to the new project.')
    args = parser.parse_args()

    try:
        path = args.path
        if path[-1] != os.path.sep:
            path = path + os.path.sep

        os.makedirs(path, exist_ok=True)

        for dir in dir_list:
            os.makedirs(path + dir, exist_ok=True)

        shutil.copyfile(os.path.dirname(os.path.realpath(__file__)) + '/main.c', path + 'src/main.c')

        for file in glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/class_embuche/c_toolbox/', '*.*')):
            shutil.copy(file, path + 'src/')
    except Exception as e:
        print('[-] Error while creating the new project structure.')
        exit()
