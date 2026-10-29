#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main ( ) {
  int a [N];
  int b [N];
  //@ admit \separated(a+(0 .. N-1), b+(0 .. N-1));
  int incr = unknown();
  int i = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer j; 0 <= j < i ==> a[j] == 42;
    loop assigns i, a[0 .. N-1];
    loop variant N - i;
  */
  while ( i < N ) {
    a[i] = 42;
    i = i + 1;
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer j; 0 <= j < N ==> a[j] == 42;
    loop invariant \forall integer j; 0 <= j < i ==> b[j] == a[j];
    loop assigns i, b[0 .. N-1];
    loop variant N - i;
  */
  for ( i = 0 ; i < N ; i++ ) {
    b[i] = a[i];
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer j; 0 <= j < N ==> a[j] == 42;
    loop invariant \forall integer j; 0 <= j < i ==> b[j] == 42 + incr;
    loop invariant \forall integer j; i <= j < N ==> b[j] == 42;
    loop assigns i, b[0 .. N-1];
    loop variant N - i;
  */
  for ( i = 0 ; i < N ; i++ ) {
    b[i] = b[i] + incr;
  }
  int x;
  /*@
    loop invariant 0 <= x <= N;
    loop invariant \forall integer j; 0 <= j < N ==> b[j] == 42 + incr;
    loop assigns x;
    loop variant N - x;
  */
  for ( x = 0 ; x < N ; x++ ) {
    //@ assert(b[x] == 42 + incr  );
  }
  return 0;
}
