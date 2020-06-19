#ifndef UTILS_H
#define UTILS_H
#ifndef CONSTS_H
	#include "cryptage.h"
#endif

void save_binary();
unsigned char * get_text_hash();
void preparing_timestamp(union SALT *salt);
void generate_key(unsigned char *new_key, union SALT *salt);
void write_to_binary(char *what, int size, unsigned long offset);

#endif /* UTILS_H */
