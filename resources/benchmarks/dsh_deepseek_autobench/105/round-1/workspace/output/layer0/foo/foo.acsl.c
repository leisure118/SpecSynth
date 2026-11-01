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


void foo(int n);

/* === Target: foo === */
/*@ requires n >= 0; */
void foo(int n) {
  int x = 0;
  
  /*@
    loop invariant 0 <= x <= n;
    loop assigns x;
    loop variant n - x;
  */
  while (x < n) {
    x = x + 1;
  }
  // post-condition
  if (n >= 0) {
    //@ assert(x == n);
  }
}
