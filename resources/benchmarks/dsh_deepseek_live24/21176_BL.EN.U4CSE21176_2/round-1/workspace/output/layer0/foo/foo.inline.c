/* Auto-generated minimal verifiable slice */
/* Target function: foo */
/* Mode: inline */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


int foo(int a,int b);

/* === Target: foo === */
int foo(int a,int b){
if(a>=0){
a++;
}
else{
a+=b;
}
return a;
}
