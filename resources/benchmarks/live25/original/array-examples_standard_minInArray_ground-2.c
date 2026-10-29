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
  int min = 0;
	for(int j = 0; j < N; j++)
	{
	  a[j] = unknown();
	}
  int i = 0;
  while ( i < N ) {
    if ( a[i] < min ) {
      min = a[i];
    }
    i = i + 1;
  }
  int x;
  for ( x = 0 ; x < N ; x++ ) {
    //@ assert(a[x] >= min  );
  }
  return 0;
}
