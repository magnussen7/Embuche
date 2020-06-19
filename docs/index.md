# Embuche overview

## Summary

- [Obstructing code analysis](./index.md#obstructing-code-analysis)
- [Detecting debuggers](./index.md#detecting-debuggers)
- [GCC options](./index.md#gcc-options)
- [File format hacks](./index.md#file-format-hacks)
- [Packer](./index.md#packer)

## Obstructing code analysis

Some anti-reversing techniques can only be set within the source code, to help you obstructing code analysis and tricking disassemblers you'll find a collection of C examples in the *snippets/* directory.

Here's the current snippets:

- **Jump over invalid bytes** (`always_follow_conditionnals.c`): Write some assembly that will be interpreted by the dissassembler but won't be executed by our program, this invalid bytes will be processed by the disassembler and mess with the disassembly it produces.  [MORE](./obstructing-code-analysis.md#always-follow-the-conditional)
- **Early return** (`early_return.c`): Trick the disassembler and prevent it to disassemble a function by forcing it to exit a function earlier. [MORE](./obstructing-code-analysis.md#early-return)
- **Indirect call** (`indirect_call.c`): Indirect call to function to limit cross-references in disassemblers.  [MORE](./obstructing-code-analysis.md#pointer-function-calls)
- **INT3** (`int3.c`): Stop the debugger if there's one attached. [MORE](./obstructing-code-analysis.md#int3)
- **Overlapping instructions** (`overlapping_instructions.c`): Write code that is executed twice but represents two different instructions.  [MORE](./obstructing-code-analysis.md#overlapping-instructions)
- **Xor stacked string** (`xor_stack_string.c`): Create xor stacked strings to prevent `strings`.
You can use `tools/c_xor.py.` to generate the C code. [MORE](./obstructing-code-analysis.md#prevent-strings)

## Detecting Debuggers

Some anti-debugging techniques can only be set in the C code. We've created a list of functions to detect debuggers.

The functions are located in `anti_debug.c`, this file will be automatically added in the `src` folder of your project at compilation, so if you want to use this function you just have to add the following lines at the start of your program:

```c
#include "anti_debug.h"

void __attribute__((constructor)) before_main()
{
  embuche_checker(1, 1, 1, 1, 1, 1);
}
```

Here's the prototype of `embuche_checker`:

`void embuche_checker(int dumpable, int ptrace, int file_descriptor, int pid, int ppid, int ld_preload)`

If you want to use an option, set the parameter to `1`.

Here's the techniques used to detect debugging:

- **dumpable**: Disable process memory dump. [MORE](./detect-debug.md#disable-core-dump)
- **ptrace**: Check if *ptrace* is already attached or not. **CAUTION: DON'T USE THIS OPTIONS IF YOU'VE IMPLEMENTED INT3 TECHNIQUE**. [MORE](./detect-debug.md#attach-to-ptrace)
- **file_descriptor**: Count the number of file descriptor to check if GDB is used. **CAUTION: THIS OPTIONS CANNOT BE SET WITH THE PACKER**. [MORE](./detect-debug.md#file-descriptor)
- **pid**: Check the process name to see if it's GDB. [MORE](./detect-debug.md#detect-GDB-by-its-pid)
- **ppid**: Check the name of the parent process to see if it's GDB. [MORE](./docs/detect-debug.md#check-the-parent-name)
- **ld_preload**: Check the environment variables to detect LD_PRELOAD. [MORE](./detect-debug.md#detect-ld_preload)

## GCC Options

The options used during the compilation modify the final binary, some of these options can give away a lot of information and help an attacker, others can strip away all unnecessary information, making the task of the attacker much harder.

Here's the list of GCC flags in Embuche by default:

- **Wall**: Show all warnings.
- **Wextra**: Show extra warnings (unused etc).
- **Wshadow**: Show local variable or type declaration that shadows other variables.
- **g0**: Disable debug informations. [MORE](./compiler-options.md#debugging-information)
- **std=gnu11**: C language dialect.

Available options for compilation:

- **strip** (-s): Remove `.symtab` section. [MORE](./compiler-options.md#delete-the-symbol-table-strip)
- **symbols_hidden** (-fvisibility=hidden): Hide `.dynsym` section. [MORE](./compiler-options.md#hide-symbol)
- **optimize** (-O3): Optimize code (level 3). [MORE](./compiler-options.md#optimization)
- **unroll_loops** (-funroll-all-loops): Undo loop structures. [MORE](./compiler-options.md#unroll-loops)
- **static** (-s): Use static dependencies instead of external ones (musl). [MORE](./compiler-options.md#static-compilation)

## File Format Hacks

It's possible to modify the ELF data structures after compilation in order to mess with disassemblers and make the reverse of a program harder.


Every techniques has a stand-alone script that you can use, there are located in `class_embuche/cmake_bakery/hellf_scripts`.

Each script takes an ELF as argument, for example:

```
./class_embuche/cmake_bakery/hellf_scripts/endianness_changer.py ./bin/myprogram
```


Here's the techniques available:

- **endianness** (`endianness_changer.py`): Change the endianness in the ELF header from little to big endian. [MORE](./docs/file-format-hacks.md#change-the-endianness)
- **remove_section_header** (`remove_sections.py`): Remove the section header table. [MORE](./docs/file-format-hacks.md#remove-section-header-table)
- **flip_sections_flags** (`flip_sections_flags.py`): Create a fake *.text* section with *RX* instead of *RW* and fake *.data* section with *RW* instead of *RX*. [MORE](./docs/file-format-hacks.md#create-fake-sections)
- **hide_entry_point** (`hide_entry_point.py`): Create a fake *.data* section that override the entry point. [MORE](./docs/file-format-hacks.md#hide-the-entry-point)
- **mixing_symbols** (`mixing_symbols_table.py`): Create a fake *.dynsym* section and mix symbols names. [MORE](./docs/file-format-hacks.md#mix-symbol-table)

To use *remove_section_header* & *flip_sections_flags* you must previously use *remove_section_header*.

If you want to combine *flip_sections_flags* & *hide_entry_point*, run `remove_section_header.py` and then `flip_sections_flags_and_hide_entry_point.py` (combination of *flip_sections_flags* and *hide_entry_point in one script*).

## Packer

A metamorphic packer is available in Embuche. This packer will load your binary and cipher it (AES 256 bits CBC).

If you decide to use the packer, your program will be ciphered and stored in a section of our packer. When you will execute your program the packer will copy itself in memory, unciphered your program and write it on the disk for execution.

Beside cipher your binary, the packer will also ensure its integrity. The encryption keys used for the encryption are based on the SHA sum of the `.text` section, so if the packer or your program is being debugged the SHA sum will be different of the one used for decryption.

There's two set of keys used by the packer to decipher the program:

- The SHA sum of the current `.text` section.
- The previous SHA sum of the `.text` section XOR'ed with the timestamp of the last run

The ELF of the packer can be modified with the `packer_embuche` options.
If this options is set the following techniques will be applied on the packer that contains your program:

- **endianness**: Change the endianness in the ELF header from little to big endian.
- **remove_section_header**: Remove the section header table.
- **flip_sections_flags**: Create a fake *.text* section with *RX* instead of *RW* and fake *.data* section with *RW* instead of *RX*.
- **hide_entry_point**: Create a fake *.data* section that override the entry point.

[MORE](./packer.md)
