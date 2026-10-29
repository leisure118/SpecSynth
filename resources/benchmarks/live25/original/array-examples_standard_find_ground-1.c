#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main ( ) {
  int a[N]; int e = unknown();
  int i = 0;
  int j;
  for ( j = 0 ; j < N; j++ ) {
    a[j] = unknown();
  }
  while( i < N && a[i] != e ) {
    i = i + 1;
  }
  int x;
  for ( x = 0 ; x < i ; x++ ) {
    //@ assert(a[x] != e  );
  }
  return 0;
}
