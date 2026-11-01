/* Auto-generated minimal verifiable slice */
/* Target function: func */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

/*@
logic integer ax_b(integer a,integer x,integer b) = a*x+b;
*/
int func(int a,int x);

/* === Target: func === */
/*@
  assigns \nothing;
  ensures \result == ax_b(a,x,4);
*/
int func(int a,int x){
return a*x+4;
}
