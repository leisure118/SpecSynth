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
	  loop invariant 0 <= i <= N;
	  loop assigns i, A[0 .. N-1];
	  loop variant N - i;
	*/
	for (i = 0; i < N ; i++ ) {
    A[i] = unknown();
  }
  /*@
    loop invariant 0 <= i <= N/2;
    loop invariant \forall integer j; 0 <= j < i ==> A[j] == A[N-j-1];
    loop assigns i, A[0 .. N/2-1];
    loop variant N/2 - i;
  */
  for (i = 0; i < N/2 ; i++ ) {
    A[i] = A[N-i-1];
  }
  int x;
  /*@
    loop invariant 0 <= x <= N/2;
    loop invariant \forall integer j; 0 <= j < N/2 ==> A[j] == A[N-j-1];
    loop assigns x;
    loop variant N/2 - x;
  */
  for ( x = 0 ; x < N/2 ; x++ ) {
    //@ assert(A[x] == A[N - x - 1]  );
  }
  return 0;
}
