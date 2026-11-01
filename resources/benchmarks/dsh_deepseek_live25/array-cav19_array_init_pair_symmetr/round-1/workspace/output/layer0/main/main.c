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
  int a[N];
  int b[N];
  int c[N];
  int x= unknown();
  for(i=0;i<N;i++) {
    x = unknown();
    //@ assert (x > -100000 && x < 100000);
    a[i]=x;
    b[i]=-x;
  }
  for(i=0;i<N;i++){
    c[i]=a[i]+b[i];
  }
  for(i=1;i<N;i++){
    //@ assert(c[i] == 0);
  }
  return 0;
}
