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
  /*@
    loop invariant 0 <= i <= N;
    loop invariant j >= 0;
    loop invariant \forall integer t; 0 <= t < i ==> a[t] >= 0;
    loop assigns i, x, j, a[0 .. N-1];
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    x=unknown();
    if(x) break;
    a[i]=j;
    j=j+i;
  }
  /*@
    loop invariant 1 <= k <= i;
    loop invariant \forall integer t; 0 <= t < i ==> a[t] >= 0;
    loop assigns k;
    loop variant i - k;
  */
  for(int k=1;k<i;k++){
    //@ assert(a[k]>=0);
  }
  return 0;
}
