#include <stdint.h>
typedef uint8_t u8; typedef uint32_t u32;
static int f(const u8 *buf, u32 len)
  /*@ requires len == 0 || \valid_read(buf + (0 .. len-1)); */
{
  return 0;
}
