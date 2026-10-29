#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
int main( ) {
  int a[SIZE];
  int b[SIZE];
	for (int j = 0; j < SIZE ; j++ ) {
    a[j] = unknown();
		b[j] = unknown();
  }
  int i = 0;
  int rv = 1;
  while ( i < SIZE ) {
    if ( a[i] != b[i] ) {
      rv = 0;
    }
    i = i+1;
  }
  if ( rv ) {
    int x;
    for ( x = 0 ; x < SIZE ; x++ ) {
      //@ assert(a[x] == b[x]  );
    }
  }
  return 0;
}
