/* Auto-generated minimal verifiable slice */
/* Target function: main */
/* Mode: inline */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


extern int unknown();

int main();

/* === Target: main === */
int main() {
  int sn = 0;
  int x = 0;
  
  while (unknown()) {
    x = x + 1;
    sn = sn + 1;
  }
  // post-condition
  if (sn != x) {
    //@ assert(sn == -1);

  }
}
