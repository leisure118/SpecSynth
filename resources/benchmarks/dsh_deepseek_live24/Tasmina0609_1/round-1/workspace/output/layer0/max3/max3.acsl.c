/* Auto-generated minimal verifiable slice */
/* Target function: max3 */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

/*@
  assigns \nothing;
  ensures \result >= a;
  ensures \result >= b;
  ensures \result >= c;
  ensures \result == a || \result == b || \result == c;
*/
int max3(int a,int b,int c);

/* === Target: max3 === */
/*@
  assigns \nothing;
  ensures \result >= a;
  ensures \result >= b;
  ensures \result >= c;
  ensures \result == a || \result == b || \result == c;
*/
int max3(int a,int b,int c) {
      int max;
      if((a >= b) && (a >= c)) {
        max = a;
      }
      else if((b >= a) && (b >= c)) {
        max = b;
      }
      else if((c >= a) && (c >= b)) {
        max = c;
      }
    return max;
}
