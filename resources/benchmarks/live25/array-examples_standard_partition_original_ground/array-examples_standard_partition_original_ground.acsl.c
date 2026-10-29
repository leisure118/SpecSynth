#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main( ) {
  int aa[N];
  int a = 0;
  int b = 0;
  int c = 0;
  int bb[N];
  int cc[N];
  //@ admit \separated(aa+(0 .. N-1), bb+(0 .. N-1), cc+(0 .. N-1));
	/*@
	  loop invariant 0 <= i <= N;
	  loop assigns i, aa[0 .. N-1];
	  loop variant N - i;
	*/
	for(int i = 0; i < N; i++)
	{
	    aa[i] = unknown();
	}
  /*@
    loop invariant 0 <= a <= N;
    loop invariant 0 <= b <= a;
    loop invariant 0 <= c <= a;
    loop invariant b + c == a;
    loop invariant \forall integer j; 0 <= j < b ==> bb[j] >= 0;
    loop invariant \forall integer j; 0 <= j < c ==> cc[j] < 0;
    loop assigns a, b, c, bb[0 .. N-1], cc[0 .. N-1];
    loop variant N - a;
  */
  while( a < N ) {
    if( aa[ a ] >= 0 ) {
      bb[ b ] = aa[ a ];
      b = b + 1;
    }
    else {
      cc[ c ] = aa[ a ];
      c = c + 1;
    }
    a = a + 1;
  }
  int x;
  /*@
    loop invariant 0 <= x <= b;
    loop invariant \forall integer j; 0 <= j < b ==> bb[j] >= 0;
    loop assigns x;
    loop variant b - x;
  */
  for ( x = 0 ; x < b ; x++ ) {
    //@ assert(bb[ x ] >= 0  );
  }
  /*@
    loop invariant 0 <= x <= c;
    loop invariant \forall integer j; 0 <= j < c ==> cc[j] < 0;
    loop assigns x;
    loop variant c - x;
  */
  for ( x = 0 ; x < c ; x++ ) {
    //@ assert(cc[ x ] < 0  );
  }
  return 0;
}
