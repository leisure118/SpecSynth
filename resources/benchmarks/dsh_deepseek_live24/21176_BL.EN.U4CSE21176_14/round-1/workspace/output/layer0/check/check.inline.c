/* Auto-generated minimal verifiable slice */
/* Target function: check */
/* Mode: inline */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


int check(int val);

/* === Target: check === */
int check(int val){
if(val>0)
return val;
else if(val<0)
return -val;
else
return 0;
}
