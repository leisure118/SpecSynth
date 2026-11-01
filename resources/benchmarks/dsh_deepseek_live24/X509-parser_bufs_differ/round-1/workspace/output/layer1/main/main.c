/* Auto-generated minimal verifiable slice */
/* Target function: main */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


int main();

/* --- Dependency: bufs_differ (stub) --- */
/* TODO: add ACSL contract here */
int bufs_differ(const u8 *b1, const u8 *b2, u32 n);

/* === Target: main === */
int main() {
  u8 b1[10] = {1,2,3,4,5,6,7,8,9,10};
  u8 b2[10] = {10,9,8,7,6,5,4,3,2,1};
  u8 b3[10] = {1,2,3,4,5,6,7,8,9,10};
  u32 n = 10;
  int ret1 = bufs_differ(b1, b3, n);
  //@ assert ret1 == 0;
  int ret2 = bufs_differ(b1, b2, n);
  //@ assert ret2 == 1;
  return 0;
}
