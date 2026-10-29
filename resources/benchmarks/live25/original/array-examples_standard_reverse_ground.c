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
	for( i = 0 ; i < N ; i++ ) {
    a[i] = unknown();
  }
  for( i = 0 ; i < N ; i++ ) {
    b[i] = a[N-i-1];
  }
  int x;
  for ( x = 0 ; x < N ; x++ ) {
    //@ assert(a[x] == b[N-x-1]  );
  }
  return 0;
}
