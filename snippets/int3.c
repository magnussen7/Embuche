#include<signal.h> // include this in your .c file

// be careful not to use this anti-debug with the "ptrace" option in embuche_checker()


// define this function above the main
void int3_shield(int signo);

int main(int argc, char **argv){
    
    signal(SIGTRAP, int3_shield); // place this line at the beginning of your main() function
    __asm__("int3"); // Place this line wherever you want in your program, it will stop the debugger in its tracks.
    // you can put it multiple times if you want, try not to place it in "sensitive areas" where the code is important
    
    return 0;
}

// put this in your .h or in your code
void int3_shield(int signo){
}
