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


extern int unknown1();
extern int unknown2();

int main();

/* === Target: main === */
int main()
{
  int i;
  int j=unknown1();
  int n=unknown2();
  //@ assert(n < 100000);
  int a[n];
  //@ assert(j>0 && j < 10000);
  for(i=1;i<n;i++) {
    int k=unknown1();
    //@ assert(k>0 && k < 10000);
    a[i]=i+j+k;
  }
  for(i=1;i<n;i++){
    //@ assert(a[i]>=(i+2));
  }
  return 0;
}  
