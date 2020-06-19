#!/usr/bin/python3.8
# coding: utf-8
import argparse
from class_embuche.embuche import embuche

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Embuche, anti-reverse helper.')
    parser.add_argument('config_file', type=str, help='Anti-reverse compilation.')
    args = parser.parse_args()

    embuche = embuche(args.config_file)
    embuche.prepare_cmake()
    embuche.run()
