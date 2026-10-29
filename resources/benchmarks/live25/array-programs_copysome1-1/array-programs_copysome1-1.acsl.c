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
  int i; 
  int z;
  z = 150000;
  //@ admit \separated(a1+(0 .. N-1), a2+(0 .. N-1));
  /*@
    loop invariant 0 <= i <= N;
    loop assigns i, a1[0 .. N-1], a2[0 .. N-1];
    loop variant N - i;
  */
  for ( i = 0 ; i < N ; i++ ) {
         a1[i] = unknown();
	 a2[i] = unknown();
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
  int x;
  /*@
    loop invariant 0 <= x <= N;
    loop invariant \forall integer j; 0 <= j < N && j != z ==> a1[j] == a2[j];
    loop assigns x;
    loop variant N - x;
  */
  for ( x = 0 ; x < N ; x++ ) {
      if (x != z){
    //@ assert(a1[x] == a2[x]  );
      }
  }
  return 0;
}
