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


void check(int a,int x,int y);

/* --- Dependency: func (stub) --- */
/* TODO: add ACSL contract here */
int func(int a,int x);

/* === Target: check === */
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
