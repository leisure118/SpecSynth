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
void foo(int n) {
  int i = 1;
  int sn = 0;
  
  /*@ loop invariant 1 <= i;
      loop invariant i <= n + 1;
      loop invariant sn == i - 1;
      loop assigns i, sn;
      loop variant n + 1 - i; */
  while (i <= n) {
    i = i + 1;
    sn = sn + 1;
  }
  // post-condition
  if (sn != 0) {
    //@ assert(sn == n);
  }
}
