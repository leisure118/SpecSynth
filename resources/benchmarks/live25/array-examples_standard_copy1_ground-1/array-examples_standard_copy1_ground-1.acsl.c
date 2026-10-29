#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main( ) {
  int a1[N];
  int a2[N];
  int a;
  /*@
    loop invariant 0 <= a <= N;
    loop assigns a, a1[0 .. N-1];
    loop variant N - a;
  */
  for ( a = 0 ; a < N ; a++ ) {
      a1[a] = unknown();
  }
  int i;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer j; 0 <= j < i ==> a2[j] == a1[j];
    loop assigns i, a2[0 .. N-1];
    loop variant N - i;
  */
  for ( i = 0 ; i < N ; i++ ) {
    a2[i] = a1[i];
  }
  int x;
  /*@
    loop invariant 0 <= x <= N;
    loop invariant \forall integer j; 0 <= j < N ==> a1[j] == a2[j];
    loop assigns x;
    loop variant N - x;
  */
  for ( x = 0 ; x < N ; x++ ) {
    //@ assert(a1[x] == a2[x]  );
  }
  return 0;
}
