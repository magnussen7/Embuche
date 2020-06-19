#!/usr/bin/python3.8
# coding: utf-8
import argparse
import sys
import os
from Hellf import ELF
from huepy import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Endianness Changer')
    parser.add_argument('binary', type=str, help='Binary to change endianness')
    args = parser.parse_args()

    if os.path.abspath(args.binary):
        hellf = ELF(args.binary)
        # We change the endianness in the ELF header from little to big endian (Fifth byte)
        hellf.elf_data = hellf.elf_data[:5] + b"\x02" + hellf.elf_data[6:]
        open(args.binary, "wb").write(hellf.elf_data + b"\n")
        print(good("file saved to : {}".format(args.binary)))
    else:
        print('Error, binary doesn\'t exist')
