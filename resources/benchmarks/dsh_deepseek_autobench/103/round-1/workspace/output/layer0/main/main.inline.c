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


int main();

/* === Target: main === */
int main() {
  int x = 0;
  
  while (x < 100) {
    x = x + 1;
  }
  // post-condition
  //@ assert(x == 100);
}
