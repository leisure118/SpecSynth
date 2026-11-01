/* Auto-generated minimal verifiable slice */
/* Target function: Sqrt */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>
#include <math.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

double Sqrt(double x);

/* === Target: Sqrt === */
/*@
  requires \is_finite(x) && x >= 0.0;
  assigns \nothing;
  ensures \result == sqrt(x);
*/
double Sqrt(double x){	
	return sqrt(x);
}
