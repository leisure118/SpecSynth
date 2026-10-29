#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main( ) {
  int a1[N];
  int a2[N];
  int a;
  for ( a = 0 ; a < N ; a++ ) {
      a1[a] = unknown();
  }
  int i;
  for ( i = 0 ; i < N ; i++ ) {
    a2[i] = a1[i];
  }
  int x;
  for ( x = 0 ; x < N ; x++ ) {
    //@ assert(a1[x] == a2[x]  );
  }
  return 0;
}
