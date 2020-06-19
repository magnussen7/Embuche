# Compiler Options

## Summary

- [TL;DR](compiler-options.md#tl-dr)
- [Target](compiler-options.md#target)
- [Debugging information](compiler-options.md#debugging-information)
- [Delete the symbol table (strip)](compiler-options.md#delete-the-symbol-table-strip)
- [Hide symbol](compiler-options.md#hide-symbol)
- [Optimization](compiler-options.md#optimization)
- [Unroll loops](compiler-options.md#unroll-loops)
- [Static compilation](compiler-options.md#static-compilation)

## TL;DR

- Do not use `-g`, it gives away information on the program and who wrote it
- Strip the binary with `-s` to remove symbols table
- Hide symbols with `-fvisibility`
- Optimize the code with `-O3` to make it harder to reverse
- Unroll the loops with `-funroll-all-loops` to create a longer code and harder to reverse
- Use static dependencies with `-s` to prevent LD_PRELOAD techniques for example

## Target

During this serie, we'll use the following code, *crackme.c*, as an example:

```c
#include <stdio.h>
#include <string.h>

int check_password(const char* p_password)
{
  char magnupass[9] = "MagnuB33r";
  return memcmp(magnupass, p_password, 9) != 0;
}

int main (int argc, char** argv) {

    if (argc != 2) {
        printf("Need exactly one argument.\n");
        return -1;
    }

    if (check_password(argv[1])) {
        printf("No, %s is not correct.\n", argv[1]);
        return 1;
    } else {
        printf("Yes, %s is correct!\n", argv[1]);
    }
    return 0;
}
```

The default *CMake* file is:

```
project(crackme)
cmake_minimum_required(VERSION 3.0)

set(CMAKE_C_FLAGS "-Wall -Wextra -Wshadow -std=gnu11")

add_executable(${PROJECT_NAME} src/${PROJECT_NAME}.c)
```

The arborescence of the project:

```
.
├── build
├── CMakeLists.txt
└── src
    └── crackme.c
```

If you want to compile the program:

```bash
magnussen@funcMyLife:~/embuche/build$ cmake ..; make
```

## Debugging information

Debugging information are really useful for a developer, it allows him to find the exact line where a variable was defined, track down the flow of an error, see the parameters of a function etc.

GCC creates several sections to store this information. All these sections start with *.debug_*.

An attacker might be interested by in the *.debug_info* section. This section contains:

- The absolute path to the source file (The name of the developer might be in that path).
- The absolute path to the compilation directory (The version of gcc is in that path).
- The C version that has been used.
- The exact line where a variable was defined.

An attacker can retrieve useful information with `objdump` (The output has been truncated):

```bash
magnussen@funcMyLife:~/embuche/build$ objdump --dwarf=info ./crackme
Contents of the .debug_info section:
  Compilation Unit @ offset 0x0:
   Length:        0x38a (32-bit)
   Version:       4
   Abbrev Offset: 0x0
   Pointer Size:  8
 <0><b>: Abbrev Number: 1 (DW_TAG_compile_unit)
    <c>   DW_AT_producer    : (indirect string, offset: 0x8d): GNU C11 7.5.0 -mtune=generic -march=x86-64 -g -std=gnu11 -fstack-protector-strong
    <10>   DW_AT_language    : 12	(ANSI C99)
    <11>   DW_AT_name        : (indirect string, offset: 0xc): /home/magnussen/crackme/src/crackme.c
    <15>   DW_AT_comp_dir    : (indirect string, offset: 0x219): /home/magnussen/crackme/build
    <19>   DW_AT_low_pc      : 0x93a
    <21>   DW_AT_high_pc     : 0x110
    <29>   DW_AT_stmt_list   : 0x0
```

> DWARF: DWARF stands for "Debugging With Attributed Record Formats" and is the default format GCC uses to store debugging information.

With this output we know that the code was compiled with GCC7.5, the program was written in C99 and the author is probably Magnussen (duh...)

The debugging information shouldn't be present in a final program. To prevent that, either don't set the `-g` option or set `-g0`.

## Delete the symbol table (strip)

Symbols can be variable or functions for example, they're defined into two sections of an ELF:

- **.symtab**, not loaded in memory
- **.dynsym**, loaded in memory at runtime.

These sections contain valuable information on symbols like their names, types, address etc.

An attacker can retrieve information on symbols with `readelf` (The output has been truncated):

```bash
magnussen@funcMyLife:~/embuche/build$ readelf --sym ./crackme

Symbol table '.dynsym' contains 23 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
    11: 0000000000201000     0 NOTYPE  GLOBAL DEFAULT   23 __data_start
    12: 0000000000201018     0 NOTYPE  GLOBAL DEFAULT   24 _end
    13: 000000000000093a   133 FUNC    GLOBAL DEFAULT   14 check_password
    14: 0000000000201000     0 NOTYPE  WEAK   DEFAULT   23 data_start
    15: 0000000000000ad0     4 OBJECT  GLOBAL DEFAULT   16 _IO_stdin_used
    16: 0000000000000a50   101 FUNC    GLOBAL DEFAULT   14 __libc_csu_init
    17: 0000000000000830    43 FUNC    GLOBAL DEFAULT   14 _start
    18: 0000000000201010     0 NOTYPE  GLOBAL DEFAULT   24 __bss_start
    19: 00000000000009bf   139 FUNC    GLOBAL DEFAULT   14 main
    20: 00000000000007b0     0 FUNC    GLOBAL DEFAULT   11 _init
    21: 0000000000000ac0     2 FUNC    GLOBAL DEFAULT   14 __libc_csu_fini
    22: 0000000000000ac4     0 FUNC    GLOBAL DEFAULT   15 _fini

Symbol table '.symtab' contains 67 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
    59: 0000000000201018     0 NOTYPE  GLOBAL DEFAULT   24 _end
    60: 0000000000000830    43 FUNC    GLOBAL DEFAULT   14 _start
    61: 0000000000201010     0 NOTYPE  GLOBAL DEFAULT   24 __bss_start
    62: 00000000000009bf   139 FUNC    GLOBAL DEFAULT   14 main
    63: 000000000000093a   133 FUNC    GLOBAL DEFAULT   14 check_password
    64: 0000000000000000     0 NOTYPE  WEAK   DEFAULT  UND _ITM_registerTMCloneTable
    65: 0000000000000000     0 FUNC    WEAK   DEFAULT  UND __cxa_finalize@@GLIBC_2.2
    66: 00000000000007b0     0 FUNC    GLOBAL DEFAULT   11 _init
```

Symbols can give away information on a program, for example, the name of the function `check_password` is pretty explicit.

The *.symtab* is not necessary for the execution of the program, we can remove it and so remove information on the program.

The strip option `-s` allows us to remove this section.

## Hide symbol

We saw in the last section how to remove the *.symtab* but an attacker could still retrieve valuable information with the *.dynsym* section.

The *.dynsym* is used during the execution so we can remove it but we can hide it with the `-fvisibility=hidden` option.

We can check with `readelf` if we can retrieve the symbols after that've been stripped and hidden:

```bash
magnussen@funcMyLife:~/embuche/build$ readelf --sym ./crackme

Symbol table '.dynsym' contains 21 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     0: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT  UND
     1: 0000000000000000     0 NOTYPE  WEAK   DEFAULT  UND _ITM_deregisterTMCloneTab
     2: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND puts@GLIBC_2.2.5 (2)
     3: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND __stack_chk_fail@GLIBC_2.4 (3)
     4: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND printf@GLIBC_2.2.5 (2)
     5: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND __libc_start_main@GLIBC_2.2.5 (2)
     6: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND memcmp@GLIBC_2.2.5 (2)
     7: 0000000000000000     0 NOTYPE  WEAK   DEFAULT  UND __gmon_start__
     8: 0000000000000000     0 NOTYPE  WEAK   DEFAULT  UND _ITM_registerTMCloneTable
     9: 0000000000000000     0 FUNC    WEAK   DEFAULT  UND __cxa_finalize@GLIBC_2.2.5 (2)
    10: 0000000000201010     0 NOTYPE  GLOBAL DEFAULT   23 _edata
    11: 0000000000201000     0 NOTYPE  GLOBAL DEFAULT   23 __data_start
    12: 0000000000201018     0 NOTYPE  GLOBAL DEFAULT   24 _end
    13: 0000000000201000     0 NOTYPE  WEAK   DEFAULT   23 data_start
    14: 0000000000000a80     4 OBJECT  GLOBAL DEFAULT   16 _IO_stdin_used
    15: 0000000000000a00   101 FUNC    GLOBAL DEFAULT   14 __libc_csu_init
    16: 00000000000007e0    43 FUNC    GLOBAL DEFAULT   14 _start
    17: 0000000000201010     0 NOTYPE  GLOBAL DEFAULT   24 __bss_start
    18: 0000000000000760     0 FUNC    GLOBAL DEFAULT   11 _init
    19: 0000000000000a70     2 FUNC    GLOBAL DEFAULT   14 __libc_csu_fini
    20: 0000000000000a74     0 FUNC    GLOBAL DEFAULT   15 _fini
```

Even the `main` is hidden, so GDB won't be able to break at `main` if an attacker try to debug the program.

## Optimization

> This option is sensitive, if the program is complex and not very well written it can cause errors.

During the compilation, GCC doesn't only *translate* the C code to ASM, it also performs various steps like optimization.

The optimization process aims to create the lighter and faster code as possible.

We can set the level of optimization in GCC, the most common options are: *-O1*, *-O2*, *-O3* and *-Os*.

*-O1*, *-O2* and *-Os* will create a smaller and faster code, because the code is smaller it'll be easier for an attacker to understand it.

On the other hand, the *-O3* options create a faster but longest code, the final program will be heavier, but it will also be more difficult to understand by an attacker.

## Unroll loops

As we saw in the previous section, the longer the code is, the harder is the job of the attacker.

GCC offers a nice option in order to create a bigger code, it allows us to *unroll* all the loops with *-funroll-all-loops*. This option undo the looping structure of any loop whose iterations can be determined at compile time, increasing the size of the final code.

## Static compilation

By default, a program will load external dependencies during its execution (*libc* oftenly).

An attacker can load his own dependencies and alter the behavior of a program. For example, he could load his own version of `memcmp` to print the values compared.

Here's an example:

```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <dlfcn.h>

int memcmp(const void *s1, const void *s2, size_t n)
{
  char* new_s1 = calloc(n + 1, 1);
  char* new_s2 = calloc(n + 1, 1);
  memcpy(new_s1, s1, n);
  memcpy(new_s2, s2, n);
  printf("memcmp(%s, %s, %u)\n", new_s1, new_s2, (int)n);
  free(new_s1);
  free(new_s2);
  int (*original_memcmp)(const void *s1, const void *s2, size_t n);
  original_memcmp = dlsym(RTLD_NEXT, "memcmp");
  return original_memcmp(s1, s2, n);
}
```

The CmakeFile for this program:

```
project(memcmp_hijacking.so C)
cmake_minimum_required(VERSION 3.0)
set(CMAKE_C_FLAGS "-Wall -Wextra -Wshadow -fPIC -shared -std=gnu11")
add_executable(${PROJECT_NAME} src/memcmp_hijacking.c)
target_link_libraries(${PROJECT_NAME} dl)
```

We can create a shared object library from this program and load it when we execute our `crackme`.

```bash
magnussen@funcMyLife:~/memcmp_hijacking/build$ cmake ..; make
magnussen@funcMyLife:~/embuche/build$ LD_PRELOAD=~/memcmp_hijacking/build/memcmp_hijacking.so ./crackme test
memcmp(MagnusSwitch, test, 13)
No, test is not correct.
```

The `-static` option prevents linking with the shared libraries, *libc* is not meant to be a statically link so we have to use another library like *musl*.

The program will be significantly heavier, but an attacker won't be able to load his own library.

We have to modify the CmakeFile if we want to use *musl*:

```
project(crackme)
cmake_minimum_required(VERSION 3.0)

set(CMAKE_C_COMPILER musl-gcc)

set(CMAKE_C_FLAGS "-Wall -Wextra -Wshadow -static -std=gnu11")

add_executable(${PROJECT_NAME} src/${PROJECT_NAME}.c)
```

If we try to load our own `memcmp` it fails:

```bash
magnussen@funcMyLife:~/embuche/build$ LD_PRELOAD=~/memcmp_hijacking/build/memcmp_hijacking.so ./crackme test
No, test is not correct.
```
