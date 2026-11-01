/* Auto-generated minimal verifiable slice */
/* Target function: reset */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


void reset(int* array,size_t length);

/* === Target: reset === */
/*@
  requires \valid(array + (0 .. length-1));
  assigns array[0 .. length-1];
  ensures \forall integer j; 0 <= j < length ==> array[j] == 0;
*/
void reset(int* array,size_t length){
/*@
  loop invariant 0 <= i <= length;
  loop invariant \forall integer j; 0 <= j < i ==> array[j] == 0;
  loop assigns i, array[0 .. length-1];
  loop variant length - i;
*/
for(size_t i=0;i<length;i++){
array[i]=0;}
}
