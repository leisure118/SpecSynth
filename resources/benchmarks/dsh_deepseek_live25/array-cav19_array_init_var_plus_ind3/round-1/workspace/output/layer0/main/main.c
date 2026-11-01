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


int N = 100000;

extern int unknown();

int main();

/* === Target: main === */
int main()
{
  int i;
  int j=0;
  int a[N];
  int x=unknown();
  for(i=0;i<N;i++){
    x=unknown();
    if(x) break;
    a[i]=j;
    j=j-i;
  }
  for(int k=4;k<i;k++){
    //@ assert(a[k] <= 0);
  }
  return 0;
}
