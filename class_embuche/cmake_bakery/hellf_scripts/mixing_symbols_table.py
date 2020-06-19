#!/usr/bin/python3.8
# coding: utf-8
import argparse
import sys
import os
from Hellf import ELF
from Hellf.lib.elf_structs import *
from huepy import *
import random
import copy

import ctypes as c
from collections import OrderedDict
from struct import unpack_from, pack

# Type of Symbol entry
@typemap
class Elf64_Sym(c.Structure, orginal_struct):
    """
    sections header structure
    """
    struct_description = "ELF Sections header struct"

    # typedef struct {
    #     Elf64_Word      st_name; /* Index into the object file's symbol string table */ 4
    #     unsigned char   st_info; /* Symbol's type and binding attributes: ELF64_ST_BIND(i) ((i)>>4), ELF64_ST_TYPE(i) ((i)&0xf), ELF64_ST_INFO(b,t) (((b)<<4)+((t)&0xf)) */ 1
    #     unsigned char   st_other; /* This member currently holds 0 and has no defined meaning */  1
    #     Elf64_Half      st_shndx; /* Symbol is in relation to this Section header table (index) */ 2
    #     Elf64_Addr      st_value; /* value of the associated symbol */ 8
    #     Elf64_Xword     st_size; /* number of bytes contained in the object */ 8
    # } Elf64_Sym;

    allowed_fields = OrderedDict([
        ("st_name" , c.c_uint32),
        ("st_info" , c.c_ubyte),
        ("st_other" , c.c_ubyte),
        ("st_shndx" , c.c_uint16),
        ("st_value" , c.c_uint64),
        ("st_size" , c.c_uint64),
    ])

    fields_names = allowed_fields.keys()
    _fields_ = [(name, size) for name, size in allowed_fields.items()]

    def __init__(self, test):
        c.Structure.__init__(self)
        orginal_struct.__init__(self, test)

# Stolen from Switch Hellf.lib.elf_structs
def typemap(cls):
    """
    wrapper who is incharge of adding _fmt attribute holding the struct format for each field and the struct itself and also the struct size
    """
    struct_fmt = ""
    for t, v in cls._fields_:

        if hasattr(v, "_length_"):
            fmt = str( v._length_) + v._type_._type_
        else:
            fmt = v._type_
        struct_fmt += fmt + " "
        setattr(cls, "_" + t + "_fmt", fmt)

    setattr(cls, "struct_fmt", struct_fmt)
    setattr(cls, "struct_size", c.sizeof(cls))

    return cls

# Stolen from Switch Hellf.lib.elf_structs
class orginal_struct:
    def __init__(cls, test, count=None, next_sh=None):
        for struct_field in cls.fields_names:
            fmt = getattr(cls, "_" + struct_field + "_fmt")
            offset = getattr(cls.__class__, struct_field).offset

            value = unpack_from(fmt, test, bufferoffset:=offset)

            if len(value) == 1:
                value = value[0]

            setattr(cls, struct_field, value)


    def __repr__(cls):
        msg =  cls.struct_description + "\n"
        fmt = "  {}:\t{}\n"
        for field in cls.fields_names:

            if hasattr(cls.allowed_fields[field], "_length_"):
                msg += fmt.format(field, " ".join(list(map(hex,getattr(cls, field)))))
            else:
                msg += fmt.format(field, hex(getattr(cls, field)))
        return msg

# Check if we section header exist, required section header table in file
def check_section_header(hellf):
    # Check if Section offset != 0 (No section header table)
    if hellf.Elf64_Ehdr.e_shoff == 0:
        return False

    # Check if section header's size in bytes is the size of the Section Header Structure otherwise quit
    if hellf.Elf64_Ehdr.e_shentsize != 0x40:
        return False

    return True

def append_dynsym(hellf):
    STT_NOTYPE = 0x00
    STB_GLOBAL = 0x01
    STT_FUNC = 0x02

    # Retrieve true .dynsym section header
    dynsym_header = hellf.get_section_by_name('.dynsym')

    # Retrieve section of .dynsym
    dynsym_section = hellf.elf_data[dynsym_header.sh_offset:dynsym_header.sh_offset+dynsym_header.sh_size]
    # Create Elf64_Sym for each entry of .dynsym section
    dynsym_entries = [Elf64_Sym(dynsym_section[i:i+dynsym_header.sh_entsize]) for i in range(0, len(dynsym_section), dynsym_header.sh_entsize)]

    # Point the offset of .dynsym section header to the fake .dynsym section (with mix name)
    # Dirty but otherwise the section header isn't save with Hellf
    # Equivalent of dynsym_header.sh_offset = len(hellf.elf_data)
    # Locate the sh_offset of dynsym
    dynsym_header_offset = hellf.elf_data.find(dynsym_header) + 24
    # Change sh_offset (Elf until dynsym_header_offset + 8bytes of sh_offset + rest of ELF)
    hellf.elf_data = hellf.elf_data[:dynsym_header_offset] + len(hellf.elf_data).to_bytes(8, 'little') + hellf.elf_data[dynsym_header_offset+8:]

    name_offsets = []
    fake_symbols = []

    # Retrieve for each symbol the index of the name and copy the entry
    for symbol in dynsym_entries:
        if ((symbol.st_info &0xf) == STT_NOTYPE) or ((symbol.st_info &0xf) == STB_GLOBAL) or ((symbol.st_info &0xf) == STT_FUNC):
            name_offsets.append(symbol.st_name)
            fake_symbols.append(copy.deepcopy(symbol))

    # Mix the name of symbol, we use the copy of the true symbol and mix the index for the name
    for symbol in fake_symbols:
        random.seed()
        index = random.randint(0, 250) % len(name_offsets)
        symbol.st_name = name_offsets[index]
        del name_offsets[index]
        # Add to the end of the file (where the .dynsym section point now)
        hellf.elf_data += symbol

    return hellf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mix Symbols name for this file')
    parser.add_argument('binary', type=str, help='Binary to mix symbol names')
    args = parser.parse_args()

    if os.path.abspath(args.binary):
        hellf = ELF(args.binary)

        # Check if section present in ELF
        if check_section_header(hellf):
            # Create fake dynsym section and mix names of symbols
            hellf = append_dynsym(hellf)

            # Replace the binary
            open(args.binary, "wb").write(hellf.elf_data + b"\n")
            print(good("file saved to : {}".format(args.binary)))
    else:
        print('Error, binary doesn\'t exist')
