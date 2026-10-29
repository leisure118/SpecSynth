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
	for (i = 0; i < N ; i++ ) {
    A[i] = unknown();
  }
  for (i = 0; i < N/2 ; i++ ) {
    A[i] = A[N-i-1];
  }
  int x;
  for ( x = 0 ; x < N/2 ; x++ ) {
    //@ assert(A[x] == A[N - x - 1]  ); 
  }
  return 0;
}
