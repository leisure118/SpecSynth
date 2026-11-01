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
/*@ assigns \nothing;
    ensures \result == a*x+4;
*/
int func(int a,int x);

/* === Target: check === */
/*@ requires a<=0;
    assigns \nothing;
    ensures \true;
*/
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
