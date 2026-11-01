#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main( ) {
  int A[N];
  int i;
	/*@
	  loop invariant 0 <= i <= 100000;
	  loop assigns i, A[0 .. 99999];
	  loop variant 100000 - i;
	*/
	for (i = 0; i < N ; i++ ) {
    A[i] = unknown();
  }
  /*@
    loop invariant 0 <= i <= 50000;
    loop invariant \forall integer j; 0 <= j < i ==> A[j] == A[99999-j];
    loop assigns i, A[0 .. 49999];
    loop variant 50000 - i;
  */
  for (i = 0; i < N/2 ; i++ ) {
    A[i] = A[N-i-1];
  }
  int x;
  /*@
    loop invariant 0 <= x <= 50000;
    loop invariant \forall integer j; 0 <= j < 50000 ==> A[j] == A[99999-j];
    loop assigns x;
    loop variant 50000 - x;
  */
  for ( x = 0 ; x < N/2 ; x++ ) {
    //@ assert(A[x] == A[N - x - 1]  ); 
  }
  return 0;
}
