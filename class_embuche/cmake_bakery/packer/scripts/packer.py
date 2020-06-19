#!/usr/bin/python3
from Hellf import ELF
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from hashlib import sha256
from huepy import good
from os import stat
from struct import pack
from sys import argv


def get_size_once_padded(binary, metadata_size):
    """
    Getting the size of the binary once padded.
    """
    bin_size = stat(binary).st_size

    tmp = bin_size % 16
    padding_size = 16 - tmp if tmp != 0 else 16

    return bin_size + padding_size + metadata_size


if __name__ == "__main__":
    # two ways to use this scripts
    # - 1 args, it return the size once padded of the provided binary
    # - 3 args, it encrypt the provided binary, and store it in an additional section .fini.

    if len(argv) == 2:
        print(get_size_once_padded(argv[1], 16), end="")

    elif len(argv) == 4:
        unloaded = ELF(argv[1])

        # :/
        iv = b"0123456789012345"

        surprise = unloaded.get_section_by_name(".fini.")
        text = unloaded.get_section_by_name(".text")

        # computing .text section sha256
        text_sum = sha256(text.data).hexdigest()
        print(good(".text sha256 sum : ") + text_sum)

        key = bytearray.fromhex(text_sum)

        binary_to_be_packed = pad(open(argv[2], "rb").read(), 16)

        encryptor = AES.new(key, AES.MODE_CBC, iv)

        # we are adding 16 bytes of metada, which are the place holder for the timestamp of the last run and the address of the .fini. section on disk.
        encrypted = (
            pack("<Q", 0)
            + pack("<Q", surprise.sh_offset)
            + encryptor.encrypt(binary_to_be_packed)
        )

        surprise.data = encrypted
        print(good("encrypted binary size : {}".format(len(encrypted))))

        unloaded.save(argv[3])

        # unit test
        assert (
            sha256(ELF(argv[3]).get_section_by_name(".text").data).hexdigest()
            == text_sum
        ), "The added section data seems corrupted !".upper()
