#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main( ){
  int aa [N]; 
  int a = 0;
	/*@
	  loop invariant 0 <= i <= N;
	  loop invariant \forall integer j; 0 <= j < i ==> INT_MIN <= aa[j] < INT_MAX;
	  loop assigns i, aa[0 .. N-1];
	  loop variant N - i;
	*/
	for(int i = 0; i < N; i++)
	{
	  aa[i] = unknown();
	}
  /*@
    loop invariant 0 <= a;
    loop invariant \forall integer j; 0 <= j < a ==> aa[j] >= 0;
    loop assigns a;
  */
  while( aa[a] >= 0 ) {
    a++;
  }
  int x;
  /*@
    loop invariant 0 <= x <= a;
    loop invariant \forall integer j; 0 <= j < a ==> aa[j] >= 0;
    loop assigns x;
    loop variant a - x;
  */
  for ( x = 0 ; x < a ; x++ ) {
    //@ assert(aa[x] >= 0  );
  }
  return 0;
}
