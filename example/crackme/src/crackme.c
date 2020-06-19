#include <stdio.h>
#include <string.h>
#include "anti_debug.h"
#include "xor_string.h"

void __attribute__((constructor)) before_main()
{
  embuche_checker(1, 1, 0, 1, 1, 1);
}

int check_password(const char* p_password)
{
  char magnupass[10] = {0x39, 0xbe, 0xaf, 0xc3, 0x98, 0xd9, 0x27, 0xf0, 0xc4, 0};
  char key_pass[10] = {0x74, 0xdf, 0xc8, 0xad, 0xed, 0x9b, 0x14, 0xc3, 0xb6, 0};

  return memcmp(undo_xor_string(magnupass, 10, key_pass, 10), p_password, 10) != 0;
}

int main (int argc, char** argv) {
    bool (*indirect_call)(const char*) = NULL;

    indirect_call = check_password - 0x100;

    if (argc != 2) {
        printf("Need exactly one argument.\n");
        return -1;
    }
    indirect_call = indirect_call + 0x100;

    if ((*indirect_call)(argv[1])) {
        printf("No, %s is not correct.\n", argv[1]);
        return 1;
    } else {
        printf("Yes, %s is correct!\n", argv[1]);
    }
    return 0;
}
