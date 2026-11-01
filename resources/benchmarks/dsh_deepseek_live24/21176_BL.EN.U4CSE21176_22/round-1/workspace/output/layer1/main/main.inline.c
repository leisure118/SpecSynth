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


void reset(int* array,size_t length);
int main();

void reset(int* array,size_t length){
for(size_t i=0;i<length;i++){
array[i]=0;}
}

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
