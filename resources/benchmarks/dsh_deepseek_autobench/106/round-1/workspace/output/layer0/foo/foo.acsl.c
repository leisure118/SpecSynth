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
/*@
 requires a <= m;
 requires j < 1;
 ensures a <= m;
*/
void foo(int a, int j, int m) {
    int k = 0;

    /*@
      loop invariant 0 <= k <= 1;
      loop invariant a <= m;
      loop assigns m, k;
      loop variant 1 - k;
    */
    while (k < 1) {
        if(m < a) {
            m = a;
        }
        k = k + 1;
    }
    //post-condition
    //@ assert(a <= m);
}
