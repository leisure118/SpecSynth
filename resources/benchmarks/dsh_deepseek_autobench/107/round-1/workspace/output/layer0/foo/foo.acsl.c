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


void foo(int a, int m);

/* === Target: foo === */
/*@
  requires a <= m;
*/
void foo(int a, int m) {
    int j = 0;
    int k = 0;

    /*@
      loop invariant a <= m;
      loop invariant 0 <= k <= 1;
      loop assigns k, m;
      loop variant 1 - k;
    */
    while ( k < 1) {
        if(m < a) {
            m = a;
        }
        k = k + 1;
    }

    //post-condition
    //@ assert(a <= m);
}
