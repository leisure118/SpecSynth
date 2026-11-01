/* Auto-generated minimal verifiable slice */
/* Target function: check */
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
  ensures \result == ((n % 2 == 0) ? 1 : 0);
*/
int check(int n);

/* === Target: check === */
/*@
  assigns \nothing;
  ensures \result == ((n % 2 == 0) ? 1 : 0);
*/
int check(int n){
if(n%2==0)
return 1;
else
return 0;
}
