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


int check(int n);
int main();

int check(int n){
if(n%2==0)
return 1;
else
return 0;
}

/* === Target: main === */
int main(){
int a=4;
int r=check(a);
//@assert a==4;
}
