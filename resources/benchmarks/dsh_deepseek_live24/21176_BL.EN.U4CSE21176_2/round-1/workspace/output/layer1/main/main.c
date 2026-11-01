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

/* --- Dependency: foo (stub) --- */
/*@
  requires -100 <= a <= 100;
  requires -100 <= b <= 100;
  assigns \nothing;
  ensures \result == (a >= 0 ? a + 1 : a + b);
*/
int foo(int a,int b);

/* === Target: main === */
int main(){
int x=-99;
int y=100;
int r=foo(x,y);
//@assert x==-99 && y==100 && r==1;
}
