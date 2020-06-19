#include <stdio.h>
#include <string.h>
#include "anti_debug.h"

int myfunction()
{
  return 1;
}

int __attribute__((optimize("O1"))) main (int argc, char** argv) {
  char* label_address = 0;

  /* A bit of code */
  label_address = calc_addr(((char*)&&return_here) - (unsigned long)&__executable_start);

  /* A bit of code */

  /* Early return */
  asm volatile(
  "push %0\n"
  "ret\n"
  ".string \"\xa2\x33\x04\xe5\x76\x77\xaa\x09\xba\x4b\xac\xfd\xfe\x0f\""
  :
  : "g"(label_address));

  return_here:

  /* A bit of code */

  return 0;
}
