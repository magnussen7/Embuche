#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>

#include <openssl/sha.h>

#include "consts.h"
#include "cryptage.h"
#include <stdlib.h>

unsigned char * get_text_hash() {

    unsigned char *hash = malloc(SHA224_DIGEST_LENGTH);
    if( hash == NULL) handle_error(".text hash malloc");

    do_sha256(hash, (unsigned char *) &text_addr, (long) &text_size);

    return hash;
}

void preparing_timestamp(union SALT *salt) {
	// preparing the salt which is the timestamp, I shouldn't do that but who cares
	for(int i = 0; i < 4; i++)
		salt->_byte[i + 4] = salt->_byte[i];
}

void generate_key(unsigned char *new_key, union SALT *salt) {
	// preparing the key for encryption

	preparing_timestamp(salt);
	// getting the .text section hash, as key for encryption
	do_sha256(new_key, (unsigned char *) &text_addr, (long) &text_size);

	// Xoring with timestamp
	for ( int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
		new_key[i] ^= (unsigned char) salt->_byte[i % 8];
	}
}


void save_binary (void) {

	/*
	 * As we can't write change directly to the binary as the file has a lock on it from another process which seems to be the loadder,
	 * we just remove it (yeah it's sucks) and write the (modified) image of the binary we maintain in ram
	 * */


	if (current_binary_name) {
		if (-1 == unlink(current_binary_name)) handle_error("couldn't remote ourself :(");

		int out = open(current_binary_name, O_CREAT | O_TRUNC | O_RDWR, S_IRWXU);

		if (NULL != tmp_mapped_binary && out) {
			write(out, tmp_mapped_binary, current_binary_size);
			close(out);
		} else
			handle_error("cannot write to binary");

	}
}

// write stuff to the binary image mapped in the heap then save it
void write_to_binary(char *what, int size, unsigned long offset) {

  if (current_binary_name) {

      memcpy((char *)tmp_mapped_binary + offset, what, size);

  }

}
