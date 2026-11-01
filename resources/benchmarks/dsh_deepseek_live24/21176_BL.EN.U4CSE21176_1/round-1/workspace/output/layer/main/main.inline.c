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


int max(int a,int b);
int main();

int max(int a,int b){
return a>b?a:b;
}

/* === Target: main === */
int main(){
int x=4;
int y=5;
int r=max(x,y);
//@assert x==4 && y==5;
}
