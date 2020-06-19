#ifndef CONSTS_H
#define CONSTS_H

#define METADATA_SIZE 16
#define REAL_SIZE BIN_SIZE
#define TO_BE_PACKED_SIZE (REAL_SIZE - METADATA_SIZE)



#ifdef DEBUG
	#include <stdlib.h>
	#include <stdio.h>
    #define handle_error(msg) do { perror(msg); exit(EXIT_FAILURE);} while(0)
#else
    #define handle_error(msg) do {exit(EXIT_FAILURE);} while(0)
#endif

extern char stack[REAL_SIZE] __attribute__ ((section (".fini.")));
extern unsigned char *iv;

extern char *current_binary_name;
extern void *tmp_mapped_binary;
extern int current_binary_size;

extern void *text_size;
extern void* text_addr;

#endif /* CONSTS_H */
