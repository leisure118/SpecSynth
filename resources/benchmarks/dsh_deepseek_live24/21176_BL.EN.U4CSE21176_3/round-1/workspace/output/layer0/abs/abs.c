/* Auto-generated minimal verifiable slice */
/* Target function: abs */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


int abs(int val);

/* === Target: abs === */
int abs(int val){
if(val<0)
return -val;
else
return val;
}
