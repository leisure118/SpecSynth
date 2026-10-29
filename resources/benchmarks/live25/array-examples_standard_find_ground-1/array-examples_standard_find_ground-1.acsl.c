#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main ( ) {
  int a[N]; int e = unknown();
  int i = 0;
  int j;
  /*@
    loop invariant 0 <= j <= N;
    loop assigns j, a[0 .. N-1];
    loop variant N - j;
  */
  for ( j = 0 ; j < N; j++ ) {
    a[j] = unknown();
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer k; 0 <= k < i ==> a[k] != e;
    loop assigns i;
    loop variant N - i;
  */
  while( i < N && a[i] != e ) {
    i = i + 1;
  }
  int x;
  /*@
    loop invariant 0 <= x <= i;
    loop invariant \forall integer k; 0 <= k < i ==> a[k] != e;
    loop assigns x;
    loop variant i - x;
  */
  for ( x = 0 ; x < i ; x++ ) {
    //@ assert(a[x] != e  );
  }
  return 0;
}
