#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main ( ) {
  int A[ N ];
  int B[ N ];
  int C[ N ]; 
  int i;
  int j = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop assigns i, A[0 .. N-1], B[0 .. N-1];
    loop variant N - i;
  */
for (i = 0; i < N ; i++) {
    A[i] = unknown();
    B[i] = unknown();
  }	
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant 0 <= j <= i;
	  loop invariant j <= N;
	  loop invariant \forall integer k; 0 <= k < j ==> C[k] < i;
	  loop invariant \forall integer k; 0 <= k < j ==> C[k] >= k;
	  loop invariant \forall integer k; 0 <= k < j ==> C[k] <= k + i - j;
	  loop invariant \forall integer k; 0 <= k < j ==> A[C[k]] == B[C[k]];
	  loop assigns i, j, C[0 .. N-1];
	  loop variant N - i;
	*/
	for (i = 0; i < N ; i++) {
    if ( A[i] == B[i] ) {
      C[j] = i;
      j = j + 1;
    }
  }
  int x; 
  /*@
    loop invariant 0 <= x <= j;
    loop invariant \forall integer k; 0 <= k < j ==> C[k] >= k;
    loop invariant \forall integer k; 0 <= k < j ==> C[k] <= k + i - j;
    loop assigns x;
    loop variant j - x;
  */
  for ( x = 0 ; x < j ; x++ ) {
    //@ assert(C[x] <= x + i - j  );
  }
  /*@
    loop invariant 0 <= x <= j;
    loop invariant \forall integer k; 0 <= k < j ==> C[k] >= k;
    loop invariant \forall integer k; 0 <= k < j ==> C[k] <= k + i - j;
    loop assigns x;
    loop variant j - x;
  */
  for ( x = 0 ; x < j ; x++ ) {
    //@ assert(C[x] >= x  );
  }
  return 0;
}
