#!/usr/bin/python3.8
# coding: utf-8
import argparse
import sys
import os
from Hellf import ELF
from Hellf.lib.elf_structs import *
from huepy import *
import random

# Check if we can create fake sections, required no section header table in file
def check_no_section_header(hellf):
    # Check if Section offset is 0 (No section header table)
    if hellf.Elf64_Ehdr.e_shoff != 0:
        return False

    # Check if section header's size in bytes is the size of the Section Header Structure
    if hellf.Elf64_Ehdr.e_shentsize != len(hellf.Elf64_Shdr):
        return False

    return True

# Create a fake .data section that override the entry point
def add_data_section(hellf, strings):
    PT_LOAD = 0x1
    PF_X = 0x1
    SHT_PROGBITS = 0x1
    SHF_ALLOC = 0x2
    SHF_EXECINSTR = 0x4

    for i in range(hellf.Elf64_Ehdr.e_phnum):
        # Search LOAD type Program Header
        if hellf.Elf64_Phdr[i].p_type == PT_LOAD:
            # Search Executable Segment
            if (hellf.Elf64_Phdr[i].p_flags & PF_X) == PF_X:
                data_header = Elf64_Shdr_ST()
                data_header.sh_name = len(strings)
                data_header.sh_type = SHT_PROGBITS
                # We change the RX flags for RW
                data_header.sh_flags = (SHF_ALLOC | SHF_EXECINSTR)
                random.seed()
                base = random.randint(0, 250)
                data_header.sh_addr = hellf.Elf64_Phdr[i].p_vaddr + base
                data_header.sh_offset = hellf.Elf64_Phdr[i].p_offset
                data_header.sh_size = hellf.Elf64_Phdr[i].p_filesz - base
                data_header.sh_link = 0
                data_header.sh_info = 0
                data_header.sh_addralign = 4
                data_header.sh_entsize = 0

                strings += b".data\x00"

                hellf.elf_data += data_header
    # Return the ELF with the fake .data section
    return hellf, strings

# Create a fake .text section
def add_text_section(hellf, strings):
    PT_LOAD = 0x1
    PF_X = 0x1
    SHT_PROGBITS = 0x1
    SHF_ALLOC = 0x2
    SHF_WRITE = 0x1

    for i in range(hellf.Elf64_Ehdr.e_phnum):
        # Search LOAD type Program Header
        if hellf.Elf64_Phdr[i].p_type == PT_LOAD:
            # Search Writable segment
            if (hellf.Elf64_Phdr[i].p_flags & PF_X) == 0:
                text_header = Elf64_Shdr_ST()
                text_header.sh_name = len(strings)
                text_header.sh_type = SHT_PROGBITS
                # We change the RW flags for RX
                text_header.sh_flags = (SHF_ALLOC | SHF_WRITE)
                text_header.sh_addr = hellf.Elf64_Phdr[i].p_vaddr
                text_header.sh_offset = hellf.Elf64_Phdr[i].p_offset
                text_header.sh_size = hellf.Elf64_Phdr[i].p_filesz
                text_header.sh_link = 0
                text_header.sh_info = 0
                text_header.sh_addralign = 4
                text_header.sh_entsize = 0

                strings += b".text\x00"

                hellf.elf_data += text_header

    # Return the ELF with the fake .text section
    return hellf, strings

# Create a .shstrtab with the name of our fake sections
def add_shstrtab_section(hellf, strings):
    SHT_STRTAB = 0x3

    strtab = Elf64_Shdr_ST()
    strtab.sh_name = len(strings)
    strtab.sh_type = SHT_STRTAB
    strtab.sh_flags = 0
    strtab.sh_addr = 0
    # Offset is end of file + 64 byte (Size of section header (shstrtab))
    strtab.sh_offset = len(hellf.elf_data) + 0x40
    strtab.sh_size = 0
    strtab.sh_link = 0
    strtab.sh_info = 0
    strtab.sh_addralign = 4
    strtab.sh_entsize = 0

    strings += b".shstrtab\x00"

    strtab.sh_size = len(strings)

    hellf.elf_data += strtab
    hellf.elf_data += (strtab.sh_offset - len(hellf.elf_data)) * b"\x00"

    hellf.elf_data += strings

    # Return the ELF with the fake .shstrtab section
    return hellf, strings

# Create the null section, .data, .text and shstrtab
def append_sections(hellf):
    strings = b"\x00"

    null_header = Elf64_Shdr_ST()

    hellf.elf_data += null_header
    hellf, strings = add_data_section(hellf, strings)
    hellf, strings = add_text_section(hellf, strings)
    hellf, strings = add_shstrtab_section(hellf, strings)

    return hellf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gonna flip some flags')
    parser.add_argument('binary', type=str, help='Binary to flip section flags (RX->RW, RW->RX)')
    args = parser.parse_args()

    if os.path.abspath(args.binary):
        hellf = ELF(args.binary)

        # Check if no section present in ELF
        if check_no_section_header(hellf):
            # This is dirty, but otherwise Hellf doesn't save the header only the raw data

            # Equivalent of hellf.Elf64_Ehdr.e_shoff = len(hellf.elf_data)
            # Set Section Header Table offset to end of file (we will append our fake sections there)
            e_shoff = len(hellf.elf_data).to_bytes(4, 'little')
            hellf.elf_data = hellf.elf_data[:40] + e_shoff + hellf.elf_data[44:]

            # Equivalent of hellf.Elf64_Ehdr.e_shentsize = 0x40
            # Size of Section 64bits (ELF64)
            hellf.elf_data = hellf.elf_data[:58] + b"\x40" + hellf.elf_data[59:]

            # Equivalent of hellf.Elf64_Ehdr.e_shnum = 0x4
            # We declare 4 fake section (A SHT_NULL one, .data, .text and .shstrtab)
            hellf.elf_data = hellf.elf_data[:60] + b"\x04" + hellf.elf_data[61:]

            # Equivalent of hellf.Elf64_Ehdr.e_shstrndx = 0x3
            # 3 names for our fake section
            hellf.elf_data = hellf.elf_data[:62] + b"\x03" + hellf.elf_data[63:]

            # Create fake sections
            hellf = append_sections(hellf)

            # Replace the binary
            open(args.binary, "wb").write(hellf.elf_data + b"\n")
            print(good("file saved to : {}".format(args.binary)))

    else:
        print('Error, binary doesn\'t exist')
