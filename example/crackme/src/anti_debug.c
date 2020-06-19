#include <signal.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/prctl.h>

typedef int bool;
#define true 1
#define false 0

#define check_strings(str_buff) (strstr(str_buff, "gdb") || strstr(str_buff, "ltrace") || strstr(str_buff, "strace") || (strstr(str_buff, "radare2")) || (strstr(str_buff, "ida")))

char* calc_addr(char* p_addr);
void embuche_checker();
int check_ptrace();
int dbg_file_descriptor();
int dbg_cmdline();
int dbg_getppid_name();
int various_ldpreload();

extern char* __executable_start;

char* calc_addr(char* p_addr)
{
    return p_addr + (unsigned long)&__executable_start;
}

void __attribute__((optimize("O1"))) embuche_checker(int dumpable, int ptrace, int file_descriptor, int pid, int ppid, int ld_preload)
{
  /* Overlapping Instructions */
  asm volatile(
  "mov_ins:\n"
  "mov $2283, %%rax\n"
  "xor %%rax, %%rax\n"
  "jz mov_ins+3\n"
  ".byte 0xe8\n"
  : :
  : "%rax");

  if (dumpable == 1) {
    /* prevent core dump */
    prctl(PR_SET_DUMPABLE, 0);
  }

  if (ptrace == 1) {
    if (check_ptrace() == 1)
    {
      exit(0);
    }
  }

  if (file_descriptor == 1) {
    if (dbg_file_descriptor() == 1)
    {
      exit(0);
    }
  }

  if (pid == 1) {
    if (dbg_cmdline() == 1)
    {
      exit(0);
    }
  }

  if (ppid == 1) {
    if (dbg_getppid_name() == 1)
    {
      exit(0);
    }
  }

  if (ld_preload == 1) {
    if (various_ldpreload() == 1)
    {
      exit(0);
    }
  }
}

/* Check if ptrace is already attached */
int __attribute__((optimize("O1"))) check_ptrace()
{
  /* Overlapping Instructions */
  asm volatile(
  "mov_in:\n"
  "mov $2283, %%rax\n"
  "xor %%rax, %%rax\n"
  "jz mov_in+3\n"
  ".byte 0xe8\n"
  : :
  : "%rax");
  return ptrace(PTRACE_TRACEME, 0, NULL, NULL) != 0;
}

/* 2 file descriptors when programs open with GDB. Both pointing to the program being debugged.*/
int __attribute__((optimize("O1"))) dbg_file_descriptor()
{
    /* Always Follow the Conditional */
    asm volatile(
    "xor %%rax, %%rax\n"
    "jz always_here + 1\n"
    "always_here:\n"
    ".byte 0xe8\n"
    : :
    : "%rax");

    FILE* fd = fopen("/", "r");
    int nb_fd = fileno(fd);
    fclose(fd);

    return (nb_fd > 3);
}

/* Detect GDB by the mean of /proc/$PID/cmdline, which should no be "gdb" */
int __attribute__((optimize("O1"))) dbg_cmdline()
{
    char* label_address = 0;

    char buff [24], tmp [16];
    FILE* f;

    label_address = calc_addr(((char*)&&return_here) - (unsigned long)&__executable_start);

    /* Early return */
    asm volatile(
    "push %0\n"
    "ret\n"
    ".string \"\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f\""
    :
    : "g"(label_address));

    return_here:
    snprintf(buff, 24, "/proc/%d/cmdline", getppid());
    f = fopen(buff, "r");
    if(fgets(tmp, 16, f) != NULL)
    fclose(f);

    return check_strings(tmp);
}

/* Check the parent's name */
int __attribute__((optimize("O1"))) dbg_getppid_name()
{
    char* label_address = 0;

    char buff1[24], buff2[16];
    FILE* f;

    label_address = calc_addr(((char*)&&return_here) - (unsigned long)&__executable_start);

    /* Early return */
    asm volatile(
    "push %0\n"
    "ret\n"
    ".string \"\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f\""
    :
    : "g"(label_address));

    return_here:
    snprintf(buff1, 24, "/proc/%d/status", getppid());
    f = fopen(buff1, "r");
    if(fgets(buff2, 16, f) != NULL)

    fclose(f);

    return check_strings(buff2);
}

/* Try to detect the LD_PRELOAD trick by looking into environnement variables of the program. */
int __attribute__((optimize("O1"))) various_ldpreload()
{
    /* Overlapping Instructions */
    asm volatile(
    "mov_i:\n"
    "mov $2283, %%rax\n"
    "xor %%rax, %%rax\n"
    "jz mov_i+3\n"
    ".byte 0xe8\n"
    : :
    : "%rax");

    return (getenv("LD_PRELOAD") != NULL);
}
