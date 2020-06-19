#include <stdio.h>
#include <string.h>

typedef int bool;
#define true 1
#define false 0

int myfunction()
{
  return 1;
}

int main (int argc, char** argv) {
    bool (*indirect_call)(const char*) = NULL;

    /* A bit of code */

    indirect_call = myfunction - 0x100;

    /* A bit of code */

    indirect_call = indirect_call + 0x100;

    (*indirect_call)();

    return 0;
}
