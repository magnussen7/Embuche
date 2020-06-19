#include <stdio.h>
#include <string.h>

int __attribute__((optimize("O1"))) main (int argc, char** argv) {
    /* Overlapping Instructions */
    asm volatile(
    "mov_ins:\n"
    "mov $2283, %%rax\n"
    "xor %%rax, %%rax\n"
    "jz mov_ins+3\n"
    ".byte 0xe8\n"
    : :
    : "%rax");

    /* A bit of code */

    return 0;
}
