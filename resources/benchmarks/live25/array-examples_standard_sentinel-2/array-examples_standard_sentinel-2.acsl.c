#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main ( ) {
  int a[N];
  int marker = unknown();
  int pos = unknown();
	/*@
	  loop invariant 0 <= i <= N;
	  loop assigns i, a[0 .. N-1];
	  loop variant N - i;
	*/
	for(int i = 0; i < N; i++) 
	{
	  a[i] = unknown();
	}
  if ( pos >= 0 && pos < N ) {
    a[ pos ] = marker;
    int i = 0;
    /*@
      loop invariant 0 <= i <= pos;
      loop invariant a[pos] == marker;
      loop assigns i;
      loop variant pos - i;
    */
    while( a[ i ] != marker ) {
      i = i + 1;
    }
    //@ assert(i <= pos  );
  }
  return 0;
}
