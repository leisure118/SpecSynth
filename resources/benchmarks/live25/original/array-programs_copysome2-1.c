#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 200000
int main( ) {
  int a1[N];
  int a2[N];
  int a3[N];
  int i; 
  int z;
  z = 150000;
  for ( i = 0 ; i < N ; i++ ) {
         a1[i] = unknown();
	 a2[i] = unknown();
  	 a3[i] = unknown();
  }
  for ( i = 0 ; i < N ; i++ ) {
      if (i != z)
         a2[i] = a1[i];
  }
  for ( i = 0 ; i < N ; i++ ) {
      if (i != z)
         a3[i] = a2[i];
      else
          a3[i] = a1[i];
  }
  int x;
  for ( x = 0 ; x < N ; x++ ) {
    //@ assert(a1[x] == a3[x]  );
  }
  return 0;
}
