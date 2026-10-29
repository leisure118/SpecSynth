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
  /*@
    loop invariant 0 <= i <= N;
    loop assigns i, a1[0 .. N-1], a2[0 .. N-1], a3[0 .. N-1];
    loop variant N - i;
  */
  for ( i = 0 ; i < N ; i++ ) {
         a1[i] = unknown();
	 a2[i] = unknown();
  	 a3[i] = unknown();
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer j; 0 <= j < i && j != z ==> a2[j] == a1[j];
    loop assigns i, a2[0 .. N-1];
    loop variant N - i;
  */
  for ( i = 0 ; i < N ; i++ ) {
      if (i != z)
         a2[i] = a1[i];
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer j; 0 <= j < i ==> a3[j] == a1[j];
    loop invariant \forall integer j; 0 <= j < N && j != z ==> a2[j] == a1[j];
    loop assigns i, a3[0 .. N-1];
    loop variant N - i;
  */
  for ( i = 0 ; i < N ; i++ ) {
      if (i != z)
         a3[i] = a2[i];
      else
          a3[i] = a1[i];
  }
  int x;
  /*@
    loop invariant 0 <= x <= N;
    loop invariant \forall integer j; 0 <= j < N ==> a1[j] == a3[j];
    loop assigns x;
    loop variant N - x;
  */
  for ( x = 0 ; x < N ; x++ ) {
    //@ assert(a1[x] == a3[x]  );
  }
  return 0;
}
