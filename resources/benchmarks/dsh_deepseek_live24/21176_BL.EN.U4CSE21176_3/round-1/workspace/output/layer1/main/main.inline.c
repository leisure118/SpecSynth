/* Auto-generated minimal verifiable slice */
/* Target function: main */
/* Mode: inline */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


int abs(int val);
int main();

int abs(int val){
if(val<0)
return -val;
else
return val;
}

/* === Target: main === */
int main(){
int x=4;
int r=abs(x);
//@assert x==4;
}
