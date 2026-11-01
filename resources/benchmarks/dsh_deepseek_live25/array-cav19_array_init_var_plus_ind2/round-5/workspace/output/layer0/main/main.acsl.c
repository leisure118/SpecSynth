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

/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
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
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer m; 0 <= m < i ==> a[m] == m*(m-1)/2;
    loop invariant j == i*(i-1)/2;
    loop invariant k == -i*(i-1)/2;
    loop assigns i, j, k, a[0 .. N-1];
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    x=unknown();
    if(x) break;
    a[i]=j;
    j=j+i;
    k=k-i;
  }
  /*@
    loop invariant 1 <= l <= i;
    loop invariant \forall integer m; 0 <= m < i ==> a[m] == m*(m-1)/2;
    loop invariant k == -i*(i-1)/2;
    loop invariant \forall integer m; 1 <= m < i ==> a[m] >= 0;
    loop invariant k <= 0;
    loop assigns l;
    loop variant i - l;
  */
  for(int l=1;l<i;l++){
    //@ assert(a[l]>=k);
  }
  return 0;
}
