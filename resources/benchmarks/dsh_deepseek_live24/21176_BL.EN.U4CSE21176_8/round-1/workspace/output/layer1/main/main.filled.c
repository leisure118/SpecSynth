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

/* --- Dependency: Sqrt (stub) --- */
/*@
  requires \is_finite(x) && x >= 0.0;
  assigns \nothing;
  ensures \result == sqrt(x);
*/
double Sqrt(double x);

/* === Target: main === */
int main(){
	double x = 9;
	double y;
	y = Sqrt(x);
	//@assert y == sqrt(x); 
	return 0;
}
