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


int N = 100000;

extern int unknown();

int main();

/* === Target: main === */
int main()
{
  int i;
  int j=0;
  int k=0;
  int a[N];
  int x=unknown();
  //@ loop invariant 0 <= i;
  //@ loop invariant i <= N;
  //@ loop invariant 0 <= j;
  //@ loop invariant k <= 0;
  //@ loop invariant \forall integer t; 0 <= t < i ==> a[t] >= 0;
  //@ loop assigns j,k,i,x,a[0..N-1];
  //@ loop variant N - i;
  for(i=0;i<N;i++){
    x=unknown();
    if(x) break;
    a[i]=j;
    j=j+i;
    k=k-i;
  }
  //@ loop invariant 1 <= l;
  //@ loop invariant l <= i;
  //@ loop invariant i <= N;
  //@ loop invariant k <= 0;
  //@ loop invariant \forall integer t; 0 <= t < i ==> a[t] >= 0;
  //@ loop assigns l;
  //@ loop variant i - l;
  for(int l=1;l<i;l++){
    //@ assert(a[l]>=k);
  }
  return 0;
}
