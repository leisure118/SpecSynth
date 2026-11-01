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


int main();

/* === Target: main === */
int main()
{
  int i;
  int N=100000;
  int a[N];
  int b[N];
  int c[N];
  for(i=0;i<N;i++) {
    a[i]=1;
    b[i]=2;
  }
  for(i=0;i<N;i++){
    c[i]=a[i]+b[i];
  }
  for(i=1;i<N;i++){
    //@ assert(c[i] >= 3);
  }
  return 0;
}
