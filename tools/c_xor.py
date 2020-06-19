#!/usr/bin/python3.8
# coding: utf-8
import argparse
import secrets

def xor_string(string):
    cipher = []
    key = []

    for i in range(0, len(string)):
        key.append('0x' + secrets.token_bytes(1).hex())
        cipher.append(hex(ord(string[i]) ^ int(key[i], 16)))
    cipher.append(0)
    key.append(0)

    return cipher, key

def generate_code(variable, cipher, key):
    declaration_variable = "char {0}[{1}] = {2};".format(variable, len(cipher), str(cipher).replace('[', '{').replace(']', '}').replace('\'', ''))
    declaration_key = "char {0}[{1}] = {2};".format(variable + "_key", len(key), str(key).replace('[', '{').replace(']', '}').replace('\'', ''))

    declaration = "{0}\n{1}".format(declaration_variable, declaration_key)

    unxor = "{0}[{1}] = undo_xor_string({0}, {1}, {2}, {3});".format(variable, len(cipher), variable + "_key", len(key))

    output = "Declaration:\n{0}\n\nDecryption:\n{1}".format(declaration, unxor)

    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Little helper to xor string and generate C code to unxor it.')
    parser.add_argument('variable', type=str, help='Name of the variable.')
    parser.add_argument('string', type=str, help='The string to xor.')
    args = parser.parse_args()

    if len(args.string) > 32:
        print("String is too long, must be less than 32 chars")
    else:
        cipher, key = xor_string(args.string)
        output = generate_code(args.variable, cipher, key)
        print("Don't forget to add the following header to include the xor decryption function:\n#include \"xor_string.h\"\n")
        print(output)
