#include <stdio.h>
#include <string.h>

void process_input(char *str) {
    char *ptr = NULL;
    
    // If the payload starts with a specific marker, it triggers the fault
    if (str[0] == 'X') {
        *ptr = 'A'; // Dereferencing a NULL pointer causes an instant crash
    }
    printf("Processed safely.\n");
}

int main(int argc, char *argv[]) {
    if (argc < 2) return 1;
    process_input(argv[1]);
    return 0;
}
