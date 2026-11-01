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
/*@
  requires 0 <= x <= 2;
  requires 0 <= y <= 2;
*/
void foo(int x, int y) {
  // loop body
  /*@
    loop invariant diff:
      x - y == \at(x, Pre) - \at(y, Pre);
    loop invariant mono:
      x >= \at(x, Pre) && y >= \at(y, Pre);
    loop invariant grows:
      0 <= y && 0 <= x;
    loop assigns x, y;
  */
  while (unknown()) {
    x  = x + 2;
    y  = y + 2;
  }
  // post-condition
  if (y == 0) {
    //@ assert(x != 4);
  }
}
