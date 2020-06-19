#!/usr/bin/python3.8
# coding: utf-8
import argparse
import os
from Hellf import ELF
from huepy import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Remove section header')
    parser.add_argument('binary', type=str, help='Binary to remove section header')
    args = parser.parse_args()

    if os.path.abspath(args.binary):
        hellf = ELF(args.binary)

        # Equivalent of hellf.Elf64_Ehdr.e_shoff = 0
        hellf.elf_data = hellf.elf_data[:40] + b"\x00\x00\x00\x00" + hellf.elf_data[44:]

        # Equivalent of hellf.Elf64_Ehdr.e_shentsize = 0
        # Size of Section 64bits (ELF64)
        hellf.elf_data = hellf.elf_data[:58] + b"\x00" + hellf.elf_data[59:]

        # Equivalent of hellf.Elf64_Ehdr.e_shnum = 0
        # We declare 0 fake section
        hellf.elf_data = hellf.elf_data[:60] + b"\x00" + hellf.elf_data[61:]

        # Equivalent of hellf.Elf64_Ehdr.e_shstrndx = 0
        # No name section
        hellf.elf_data = hellf.elf_data[:62] + b"\x00" + hellf.elf_data[63:]

        open(args.binary, "wb").write(hellf.elf_data + b"\n")
        print(good("file saved to : {}".format(args.binary)))
    else:
        print('Error, binary doesn\'t exist')
