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

/* --- Dependency: reset (stub) --- */
/*@
  requires \valid(array + (0 .. length-1));
  assigns array[0 .. length-1];
  ensures \forall integer j; 0 <= j < length ==> array[j] == 0;
*/
void reset(int* array,size_t length);

/* === Target: main === */
int main(){
int a[]={1,2,3,4,5};
reset(a,5);
//@ assert a[0] == 0;
//@ assert a[1] == 0;
//@ assert a[2] == 0;
//@ assert a[3] == 0;
//@ assert a[4] == 0;
}
