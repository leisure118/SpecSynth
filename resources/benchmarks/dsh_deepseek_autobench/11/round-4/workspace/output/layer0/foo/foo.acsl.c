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


extern int unknown();

void foo(int x, int y);

/* === Target: foo === */
/*@ requires 0 <= x <= 10;
    requires 0 <= y <= 10;
    assigns x, y;
 */
void foo(int x, int y) {
  // loop body
  /*@ loop invariant x - y == \at(x, Pre) - \at(y, Pre);
      loop invariant y >= \at(y, Pre);
      loop assigns x, y;
   */
  while (unknown()) {
    x  = x + 10;
    y  = y + 10;
  }
  // post-condition
  if (x == 20) {
    //@ assert(y != 0);
  }
}
