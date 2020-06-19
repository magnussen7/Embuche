#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <string.h>

#include "consts.h"
#include "cryptage.h"


char surprise_section[REAL_SIZE] __attribute__ ((section (".fini."))) = { 0 };
unsigned char *iv = (unsigned char *)"0123456789012345";

char *current_binary_name;  // store the actual binary path and name
void *tmp_mapped_binary;    // address in heap where is store the image of the binary
int current_binary_size;    // size of the binary to be packed


int main(int argc, char** argv, char **env) {

	#ifdef DEBUG
		puts("DEBUG MODE");
	#endif

    char *anon_fd_name = "acab"; // because ftp
    char fname[1024];            // store the anonymous name in /proc/pid/fd/fd

    // fetching user programme name (+ 1 to store a null byte)
    current_binary_name = (void *) malloc(strlen(argv[0]) + 1);
    if (current_binary_name == NULL ) handle_error("malloc argv name");

    strcpy(current_binary_name, argv[0]);

    // mapping binary in memory
    int fd = open(current_binary_name, O_RDONLY);
    if (fd == -1 ) handle_error("fd on packer -1");

    // get file size and reset cursor at the benining
    current_binary_size = lseek(fd, 0 , SEEK_END);
    lseek(fd, 0, SEEK_SET);

    // we gonna map the packer itself in the ram
    tmp_mapped_binary = malloc(current_binary_size);
    if (tmp_mapped_binary == NULL ) handle_error("malloc packer memory mapping");

    if ( read(fd, tmp_mapped_binary, current_binary_size) != current_binary_size)
    	handle_error("can't map binary in memory");

    // creating an anonymous file in ram
    int fd_d = memfd_create(anon_fd_name, MFD_CLOEXEC);

    if (fd_d == -1 ) handle_error("memfd_create failed");

    snprintf(fname, 1024, "/proc/%d/fd/%d", getpid(), fd_d);
    argv[0] = fname;

    // we decrypt the encrypted section, which is stored at *stack
    decrypt((unsigned char *) surprise_section, fd_d);
    execve(fname, argv, env);

#ifdef DEBUG
    // if we reach this statement it means the call to execve failed.
    puts("packee launch failed");
#endif

    return 0; // prettry straight forward
}

// I use arch btw

