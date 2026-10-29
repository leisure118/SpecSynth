#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main( ) {
  int a[ N ];
  int i = 0;
  int x;
  int y;
	/*@
	  loop invariant 0 <= i <= N;
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(int i = 0; i < N; i++) 
	{
	    a[i] = unknown();
	}
	i = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer p, q; 0 <= p <= q < i ==> a[p] <= a[q];
    loop invariant \forall integer p, q; 0 <= p < i <= q < N ==> a[p] <= a[q];
    loop assigns i, a[0 .. N-1], x, y;
    loop variant N - i;
  */
  while ( i < N ) {
    int k = i + 1;
    int s = i;
    /*@
      loop invariant i < k <= N;
      loop invariant i <= s < N;
      loop invariant \forall integer j; i <= j < k ==> a[s] <= a[j];
      loop assigns k, s;
      loop variant N - k;
    */
    while ( k < N ) {
      if ( a[k] < a[s] ) {
        s = k;
      }
      k = k+1;
    }
    if ( s != i ) {
      int tmp = a[s];
      a[s] = a[i];
      a[i] = tmp;
    }
    /*@
      loop invariant 0 <= x <= i;
      loop invariant \forall integer p, q; 0 <= p <= q < i ==> a[p] <= a[q];
      loop assigns x, y;
      loop variant i - x;
    */
    for ( x = 0 ; x < i ; x++ ) {
      /*@
        loop invariant x < y <= i;
        loop invariant \forall integer p, q; 0 <= p <= q < i ==> a[p] <= a[q];
        loop assigns y;
        loop variant i - y;
      */
      for ( y = x + 1 ; y < i ; y++ ) {
        //@ assert(a[x] <= a[y]  );
      }
    }
    /*@
      loop invariant i <= x <= N;
      loop invariant \forall integer j; i <= j < N ==> a[j] >= a[i];
      loop assigns x, y;
      loop variant N - x;
    */
    for ( x = i ; x < N ; x++ ) {
      //@ assert(a[x] >= a[i]  );
    }
    i = i+1;
  }
  /*@
    loop invariant 0 <= x <= N;
    loop invariant \forall integer p, q; 0 <= p <= q < N ==> a[p] <= a[q];
    loop assigns x, y;
    loop variant N - x;
  */
  for ( x = 0 ; x < N ; x++ ) {
    /*@
      loop invariant x < y <= N;
      loop invariant \forall integer p, q; 0 <= p <= q < N ==> a[p] <= a[q];
      loop assigns y;
      loop variant N - y;
    */
    for ( y = x + 1 ; y < N ; y++ ) {
      //@ assert(a[x] <= a[y]  );
    }
  }
  return 0;
}
