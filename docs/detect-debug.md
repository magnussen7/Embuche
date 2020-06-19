# Detect debugging

## Summary

- [TL;DR](detect-debug.md#tl-dr)
- [Attach to *ptrace*](detect-debug.md#attach-to-ptrace)
- [File descriptor](detect-debug.md#file-descriptor)
- [Detect GDB by its PID](detect-debug.md#detect-GDB-by-its-pid)
- [Check the parent name](detect-debug.md#check-the-parent-name)
- [Detect LD_PRELOAD](detect-debug.md#detect-ld_preload)
- [Disable Core Dump](detect-debug.md#disable-core-dump)
- [Final code](detect-debug.md#final-code)

## TL;DR

- GDB and others debuggers use *ptrace* call to attach a process and control its memory and registers.
- A program can only be attached by one *ptrace* call, if our program is already attached, it can't be attached by GDB.
- GDB uses two file descriptors when it debugs a program, we can check the number of file descriptors pointing to our program to detect GDB.
- We can use the proc files *cmdline* and *status* to check if our program was started by a debugger.
- We can detect the environment variables and exit if the program was started with LD_PRELOAD
- We can block memory dump with `prctl(PR_SET_DUMPABLE, 0);`

## Attach to *ptrace*

A debugger attach itself to the program it debugs with *ptrace* system call.

This system call allows one process (called the *tracer*) to observe and control the execution of another process (the *tracee*).

What's interesting for us is that a process can only be attached by one tracer. So if our process has already called *ptrace*, GDB won't be able to attach to it.

With this function we can check if *ptrace* is already attached or not.

```c
#include <sys/ptrace.h>

int check_ptrace()
{
  return ptrace(ptrace_TRACEME, 0, NULL, NULL) != 0;
}
```

If it's attached the function will return 1, otherwise 0.


## File descriptor

Another way to detect a debugger is to check the file descriptor it uses.

Normally, a program has 3 file descriptors:

- stdin
- stdout
- stderr

But, when GDB is debugging a binary, it opens 3 more file descriptors.

We can easily check how many file descriptors are opened with this function:

```c
int dbg_file_descriptor()
{
    FILE* fd = fopen("/", "r");
    int nb_fd = fileno(fd);
    fclose(fd);

    return (nb_fd > 3);
}
```

If there's more than 3 file descriptors, the program might be debugged.

## Detect GDB by its PID

We can also check if the program is being debugged by checking the command line that started the process.

When a program is executed, a directory is created in /proc with the PID of the process.

In this directory we can find multiple information on the process like names and values of the environment variables, its run state and memory usage and the command that originally started the process.

By checking the /proc/*pid*/cmdline file we can find the complete command line for the process and check if the program was started by GDB.

Here's a function that allows us to read the /proc/*pid*/cmdline and check if it was GDB that started the process.

```c
#define check_strings(str_buff) (strstr(str_buff, "gdb") || strstr(str_buff, "ltrace") || strstr(str_buff, "strace") || (strstr(str_buff, "radare2")) || (strstr(str_buff, "ida")))

int dbg_cmdline()
{
    char buff [24], tmp [16];
    FILE* f;

    snprintf(buff, 24, "/proc/%d/cmdline", getppid());
    f = fopen(buff, "r");
    fgets(tmp, 16, f);
    fclose(f);

    return check_strings(tmp);
}
```

If there's *GDB*, *ltrace*, *strace*, *radare2* or *ida* in the command line that started the process it's certainly because the program was debugged.

> We check if the program is executed by GDB, but we can prevent GDB to statically analyze it.

## Check the parent name

Another way to see if our program is being traced is to check the status file in the proc directory.

If our process is being debugged, it might have been started by GDB. The debugger will be the parent process of our program.

We can check if the parent process is GDB by checking the /proc/PID/status file of our PPID (Parent Process IDentifier).

```c
#define check_strings(str_buff) (strstr(str_buff, "gdb") || strstr(str_buff, "ltrace") || strstr(str_buff, "strace") || (strstr(str_buff, "radare2")) || (strstr(str_buff, "ida")))

int dbg_getppid_name()
{
    char buff1[24], buff2[16];
    FILE* f;

    snprintf(buff1, 24, "/proc/%d/status", getppid());
    f = fopen(buff1, "r");
    fgets(buff2, 16, f);
    fclose(f);

    return check_strings(buff2);
}
```

If *GDB*, *ltrace*, *strace*, *radare2* or *ida* is in the status file of our parent process, our program might be debugged.

## Detect LD_PRELOAD

One other common technique to dynamically debug a program is loading external dependencies to modify the behaviour of a function in the program.

As we saw in the first article of this serie, it's possible to load its own version of a function and check which values are compared when it is called for example.

One solution was to use static dependencies to block the use of external ones.

We can also check the environment variables to check if LD_PRELOAD was set.

```c
int various_ldpreload()
{
    return (getenv("LD_PRELOAD") != NULL);
}
```

If the LD_PRELOAD environment variable is set, the program might be debugged.

## Disable core dump

The previous techniques worked if the program was directly debug by GDB but its possible for an attacker to dump the memory process without controlling executing and inject it in GDB.

To prevent core dump, we can disable the *dumpable* flag of the process and avoid the generation of a memory dump.

To do so we can use the following line:

```c
#include <sys/prctl.h>

prctl(PR_SET_DUMPABLE, 0);
```

As we set the *PR_SET_DUMPABLE* flag to 0, the process cannot be dumped.

## Final code

Here's the list of all the functions we've discussed, if one of these functions returns *1* the program is being debugged, we exit the program.

```c
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

void dbg_checker();
int check_ptrace();
int dbg_file_descriptor();
int dbg_cmdline();
int dbg_getppid_name();
int various_ldpreload();

void dbg_checker()
{
  /* prevent core dump */
  prctl(PR_SET_DUMPABLE, 0);

  if (check_ptrace() == 1)
  {
    exit(0);
  }

  if (dbg_file_descriptor() == 1)
  {
    exit(0);
  }

  if (dbg_cmdline() == 1)
  {
    exit(0);
  }

  if (dbg_getppid_name() == 1)
  {
    exit(0);
  }

  if (various_ldpreload() == 1)
  {
    exit(0);
  }
}

/* Check if ptrace is already attached */
int check_ptrace()
{
  return ptrace(PTRACE_TRACEME, 0, NULL, NULL) != 0;
}

/* 2 file descriptors when programs open with GDB. Both pointing to the program being debugged.*/
int dbg_file_descriptor()
{
    FILE* fd = fopen("/", "r");
    int nb_fd = fileno(fd);
    fclose(fd);

    return (nb_fd > 3);
}

/* Detect GDB by the mean of /proc/$PID/cmdline, which should no be "gdb" */
int dbg_cmdline()
{
    char buff [24], tmp [16];
    FILE* f;

    snprintf(buff, 24, "/proc/%d/cmdline", getppid());
    f = fopen(buff, "r");
    fgets(tmp, 16, f);
    fclose(f);

    return check_strings(tmp);
}

/* Check the parent's name */
int dbg_getppid_name()
{
    char buff1[24], buff2[16];
    FILE* f;

    snprintf(buff1, 24, "/proc/%d/status", getppid());
    f = fopen(buff1, "r");
    fgets(buff2, 16, f);
    fclose(f);

    return check_strings(buff2);
}

/* Try to detect the LD_PRELOAD trick by looking into environnement variables of the program. */
int various_ldpreload()
{
    return (getenv("LD_PRELOAD") != NULL);
}
```
