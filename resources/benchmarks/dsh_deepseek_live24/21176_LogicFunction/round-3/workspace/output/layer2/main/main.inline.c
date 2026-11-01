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


int func(int a,int x);
void check(int a,int x,int y);
int main();

int func(int a,int x){
return a*x+4;
}

void check(int a,int x,int y){
int fmin,fmax;
if(x>y){
fmin=func(a,x);
fmax=func(a,y);
}
else{
fmin=func(a,y);
fmax=func(a,x);
}
//@assert fmin<=fmax;
}

/* === Target: main === */
int main(){
int w=3;
int r=4;
int s=7;
int t=func(w,r);
check(w,r,s);
}
