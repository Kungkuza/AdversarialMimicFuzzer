#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void process_input(char *str) {
    // Ensure the input string contains enough characters to read index 2 safely
    if (strlen(str) < 4) {
        printf("Payload too short, exiting safely.\n");
        return;
    }
    
    // Read the character at index 2 (skips the \x4d\x5a header bytes)
    // If this character evaluates to a space (0x20), denominator becomes 0
    int denominator = (int)str[2] - 0x20; 
    
    // Attempting division by zero triggers a SIGFPE hardware fault immediately
    int result = 1000 / denominator;
    printf("Result of operation: %d\n", result);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <input_payload>\n", argv[0]);
        return 1;
    }
    
    process_input(argv[1]);
    return 0;
}
