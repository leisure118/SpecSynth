#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main( ) {
  int a[N];
  int b[N];
  int i;
	/*@
	  loop invariant 0 <= i <= N;
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for( i = 0 ; i < N ; i++ ) {
    a[i] = unknown();
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer j; 0 <= j < i ==> b[j] == a[N-j-1];
    loop assigns i, b[0 .. N-1];
    loop variant N - i;
  */
  for( i = 0 ; i < N ; i++ ) {
    b[i] = a[N-i-1];
  }
  int x;
  /*@
    loop invariant 0 <= x <= N;
    loop invariant \forall integer j; 0 <= j < N ==> b[j] == a[N-j-1];
    loop assigns x;
    loop variant N - x;
  */
  for ( x = 0 ; x < N ; x++ ) {
    //@ assert(a[x] == b[N-x-1]  );
  }
  return 0;
}
