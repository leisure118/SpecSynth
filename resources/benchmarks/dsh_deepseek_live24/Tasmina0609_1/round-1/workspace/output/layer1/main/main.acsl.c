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

/* --- Dependency: max3 (stub) --- */
/*@
  assigns \nothing;
  ensures \result >= a;
  ensures \result >= b;
  ensures \result >= c;
  ensures \result == a || \result == b || \result == c;
*/
int max3(int a,int b,int c);

/* === Target: main === */
int main(){
    int a = 10;
    int b = 20;
    int c = 30;
    int max = max3(a,b,c);
    //@ assert max == 30;
}
