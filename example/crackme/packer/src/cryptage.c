//
// Created by switch on 6/4/20.
//
#include <stdio.h>
#include <unistd.h>
#include <math.h>
#include <string.h>
#include <time.h>

#include <openssl/conf.h>
#include <openssl/evp.h>
#include <openssl/sha.h>

#include "utils.h"
#include "cryptage.h"
#include "consts.h"

// performs sha256 of the given memory space
void do_sha256(unsigned char *hash, unsigned char *addr, long size) {

    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    SHA256_Update(&sha256, addr, size);
    SHA256_Final(hash, &sha256);
}

void decrypt(unsigned char *ciphertext, int fd_d)
{
    EVP_CIPHER_CTX *decrypt_ctx, *encrypt_ctx;

    int offset = 0;
    int decrypt_len, encrypt_len;
    int block_size = 0;

    /* +16 bytes come from EVP_XXcryptUpdate
     * it writes the 16 last bytes from the last block at the next call
     * https://security.stackexchange.com/questions/86952/why-does-the-first-call-to-decryptupdate-in-aes-cbc-return-16-fewer-bytes
     * */
    unsigned char decrypted[256+16] = {0};
    unsigned char re_encrypted_text[256+16] = {0};

    int decrypted_len, encrypted_len;
    int size_without_padding = 0;

    union SALT salt; // because I'm salted

    // key for encryption
    // come from sha256(.text) ^ timestamp
    unsigned char *key = get_text_hash();
	// new_key is the key when re encrypting the decoded stuff, it's explained later, enjoy the code
	unsigned char new_key[SHA256_DIGEST_LENGTH] = {0};

    /* if it's first run as
     *      8 bytes                 8 bytes
     * +------------------------+------------------------------------+
     * |  timestamp of last run | additionnal section offset on disk |
     * +------------------------+------------------------------------+
     * | DATAAAAAAAAAAAAAAAAAAAAAAAAAAAAA ...                        |
     * | AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACABAAAAAAAAAAAAA |
     * |  ... AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA |
     * +-------------------------------------------------------------+
     */

	unsigned long long section_offset_on_disk  = *((unsigned long long *) (ciphertext+8));

	if (section_offset_on_disk == 0) handle_error("houston, we got a probleme here");

    if ( *((unsigned long long *) ciphertext) == 0) {

        // getting the timestamp of the run
        salt._long =  (unsigned long) time(NULL);

        // writing timestamp to metadata
        write_to_binary(salt._byte, 8, section_offset_on_disk);

        // preparing the key for encryption
		generate_key(new_key, &salt);

    }

    // it's not the first run, we need to get the timestamp to get the key
    else {

        // retrieving the timestamp
        salt._long = *((unsigned long *) ciphertext);

        generate_key(key, &salt);

        // preparing the new key
        salt._long = (unsigned long) time(NULL);
        // writing timestamp to metadata
        write_to_binary(salt._byte, 8, section_offset_on_disk);

	    // preparing the key for encryption
	    generate_key(new_key, &salt);

    }

    // we skip our metada
    ciphertext += 16;

    if ( !(decrypt_ctx = EVP_CIPHER_CTX_new()) || !(encrypt_ctx = EVP_CIPHER_CTX_new()) ) handle_error("can't initiat context");


    if ( 1 != EVP_EncryptInit_ex(encrypt_ctx, EVP_aes_256_cbc(), NULL, new_key, iv)
        || 1 != EVP_DecryptInit_ex(decrypt_ctx, EVP_aes_256_cbc(), NULL, key, iv)) handle_error("can't init crypto");

    /* decrypting / encrypting routine */

    /*
     * encryption / decryption process operate by 256 bytes block
     * so we count amount of block rounded up. In all case, only the last block could have a different size
     * or just be equal to 256
     */
    for( int i = 0; i < (int) ceil(TO_BE_PACKED_SIZE / 256.0); i++ ) {

    	// would always be 256, unless it's the last block
        block_size = (TO_BE_PACKED_SIZE - (256 * i)) > 256 ?  256 : (TO_BE_PACKED_SIZE - (256 * i)) % 256 ;

        /*
         * as explained before, sometimes 16 bytes are added, but only after on call to xxxcrypt_update is made
         */
        if (i && !offset)
            offset = 16;

        if ( 1 != EVP_DecryptUpdate(decrypt_ctx, decrypted, &decrypt_len, ciphertext + (256 * i), block_size))
        	handle_error("crypto update failed");

        decrypted_len += decrypt_len;


        // re encrypting the stuff
        if(  1 != EVP_EncryptUpdate(encrypt_ctx, re_encrypted_text, &encrypt_len, decrypted + offset, block_size))
	        handle_error("crypto update failed");

        encrypted_len += encrypt_len;

		// i forgot why I added the +16, without it segfault. Better keeping it.
        unsigned long block_offset = section_offset_on_disk + 16 + (256 * i);

	    write_to_binary((char *) re_encrypted_text, block_size, block_offset);

	    // debug, could help
        // BIO_dump_fp (stdout, (const char *)decrypted + offset, block_size);
        // puts("");
        // BIO_dump_fp (stdout, (const char *)ciphertext + (256 * i), block_size);
        // puts("");
        // BIO_dump_fp (stdout, re_encrypted_text, block_size);
        // puts("");

		// PKCS padding, the last byte of decrypted data is the size in byte of padding
        size_without_padding = block_size - ((block_size != 256) ? ((int) decrypted[block_size + 8 - 1]) : 0);

        // writing the part of the ELF to our anonymous file
        write(fd_d, decrypted + offset, size_without_padding);
    }

    save_binary();

    if ( 1 != EVP_DecryptFinal_ex(decrypt_ctx, decrypted + decrypt_len, &decrypt_len)) {
	    #ifdef DEBUG
	        puts("evp_decrypt_final");
	    #endif
    }
    else {
        decrypted_len += decrypt_len;
    }

    if(1 != EVP_EncryptFinal_ex(encrypt_ctx, re_encrypted_text + encrypt_len, &encrypt_len)) {
	    #ifdef DEBUG
	        puts("evp_enrypt_final");
	    #endif

    } else {
        encrypted_len += encrypt_len;
    }

    // be nice
    EVP_CIPHER_CTX_free(decrypt_ctx);
    EVP_CIPHER_CTX_free(encrypt_ctx);
}
