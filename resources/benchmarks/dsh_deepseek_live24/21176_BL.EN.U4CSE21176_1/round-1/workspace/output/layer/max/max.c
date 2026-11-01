/* Auto-generated minimal verifiable slice */
/* Target function: max */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


int max(int a,int b);

/* === Target: max === */
int max(int a,int b){
return a>b?a:b;
}
