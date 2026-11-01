/* Auto-generated minimal verifiable slice */
/* Target function: main */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


int main();

/* --- Dependency: check (stub) --- */
/* TODO: add ACSL contract here */
void check(int a,int x,int y);

/* --- Dependency: func (stub) --- */
/* TODO: add ACSL contract here */
int func(int a,int x);

/* === Target: main === */
int main(){
int w=3;
int r=4;
int s=7;
int t=func(w,r);
check(w,r,s);
}
