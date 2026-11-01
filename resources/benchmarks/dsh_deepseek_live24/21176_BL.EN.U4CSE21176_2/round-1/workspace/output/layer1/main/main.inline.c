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


int foo(int a,int b);
int main();

int foo(int a,int b){
if(a>=0){
a++;
}
else{
a+=b;
}
return a;
}

/* === Target: main === */
int main(){
int x=-99;
int y=100;
int r=foo(x,y);
//@assert x==-99 && y==100 && r==1;
}
