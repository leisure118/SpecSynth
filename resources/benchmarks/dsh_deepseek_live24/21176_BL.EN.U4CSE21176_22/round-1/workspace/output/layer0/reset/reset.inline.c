/* Auto-generated minimal verifiable slice */
/* Target function: reset */
/* Mode: inline */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


void reset(int* array,size_t length);

/* === Target: reset === */
void reset(int* array,size_t length){
for(size_t i=0;i<length;i++){
array[i]=0;}
}
