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

/* === Target: main === */
int main()
{
  int i;
  int N=100000;
  int a[N];
  int b[N];
  int c[N];
  /*@ assert \valid(a+(0..N-1)) && \valid(b+(0..N-1)) && \valid(c+(0..N-1)); */
  /*@ assert \separated(a+(0..N-1), b+(0..N-1)) && \separated(a+(0..N-1), c+(0..N-1)) && \separated(b+(0..N-1), c+(0..N-1)); */
  for(i=0;i<N;i++) {
    /*@ loop invariant 0 <= i <= N;
        loop invariant \forall integer j; 0 <= j < i ==> a[j] == 1 && b[j] == 2;
        loop assigns i, a[0..N-1], b[0..N-1];
        loop variant N - i; */
    a[i]=1;
    b[i]=2;
  }
  for(i=0;i<N;i++){
    /*@ loop invariant 0 <= i <= N;
        loop invariant \forall integer j; 0 <= j < N ==> a[j] == 1 && b[j] == 2;
        loop invariant \forall integer j; 0 <= j < i ==> c[j] == a[j] + b[j];
        loop assigns i, c[0..N-1];
        loop variant N - i; */
    c[i]=a[i]+b[i];
  }
  for(i=1;i<N;i++){
    /*@ loop invariant 1 <= i <= N;
        loop invariant \forall integer j; 0 <= j < N ==> c[j] == 3;
        loop assigns i;
        loop variant N - i; */
    //@ assert(c[i] >= 3);
  }
  return 0;
}
