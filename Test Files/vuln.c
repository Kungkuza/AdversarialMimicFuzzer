#include <stdio.h>
#include <string.h>

void process_input(char *str) {
    char buffer[16];
    // Dangerous function! It doesn't check boundaries.
    strcpy(buffer, str); 
    printf("Processed: %s\n", buffer);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        return 1;
    }
    process_input(argv[1]);
    return 0;
}
