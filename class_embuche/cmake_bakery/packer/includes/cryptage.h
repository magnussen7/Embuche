#ifndef PACKER2_CRYPTAGE_H
#define PACKER2_CRYPTAGE_H


union SALT {
    char _byte[8];
    unsigned long _long;
};

void do_sha256(unsigned char *hash, unsigned char *addr, long size);
void decrypt(unsigned char *ciphertext, int fd_d);

#endif //PACKER2_CRYPTAGE_H
