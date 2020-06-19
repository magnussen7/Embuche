#include <stdio.h>
#include <string.h>

int __attribute__((optimize("O1"))) main (int argc, char** argv) {
    /* Always Follow the Conditional */
    asm volatile(
    "xor %%rax, %%rax\n"
    "jz always_here + 1\n"
    "always_here:\n"
    ".byte 0xe8\n"
    : :
    : "%rax");

    /* A bit of code */

    return 0;
}
