/* Auto-generated minimal verifiable slice */
/* Target function: foo */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


void foo(int a, int j, int m);

/* === Target: foo === */
void foo(int a, int j, int m) {
    int k = 0;

    while (k < 1) {
        if(m < a) {
            m = a;
        }
        k = k + 1;
    }
    //post-condition
    //@ assert(a <= m);
}
