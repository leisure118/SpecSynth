/* Auto-generated minimal verifiable slice */
/* Target function: spec_abs1 */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


long spec_abs1(int a);

/* === Target: spec_abs1 === */
/*@ assigns \nothing;
    ensures \result >= 0;
    ensures \result == (a >= 0 ? a : -a);
 */
long spec_abs1(int a)
{
   long abs;
   abs = a;
   if (a < 0) {
      abs = -abs;
   }
   return abs;
}
