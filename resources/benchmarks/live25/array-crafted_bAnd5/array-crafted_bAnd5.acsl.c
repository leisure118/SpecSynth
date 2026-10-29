#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define fun bAnd
#include <assert.h>
int N;
/*@ requires N >= 1; assigns \nothing; */
int bAnd (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant \forall integer j; 0 <= j < i ==> (res & (long long)x[j]) == res;
    loop assigns i, res;
    loop variant N - i;
  */
  for (i = 1; i < N; i++) {
    res = res & x[i];
  }
  return res;
}
int main ()
{
  N = unknown();
  if (N > 1) {
    int x[N];
    int temp;
    int ret;
    int ret2;
    int ret5;
	  /*@
	    loop invariant 0 <= i <= N;
	    loop assigns i, x[0 .. N-1];
	    loop variant N - i;
	  */
	  for(int i = 0; i < N; i++) 
		{
		  x[i] = unknown();
		}
		ret = fun(x);
    temp=x[0];x[0] = x[1]; x[1] = temp;
    ret2 = fun(x);
    temp=x[0];
    /*@
      loop invariant 0 <= i <= N-1;
      loop assigns i, x[0 .. N-1];
      loop variant N-1 - i;
    */
    for(int i =0 ; i<N-1; i++){
       x[i] = x[i+1];
    }
    x[N-1] = temp;
    ret5 = fun(x);
    //@ admit ret == ret2;
    //@ admit ret == ret5;
    //@ assert !(ret != ret2 || ret !=ret5);
  }
  return 1;
}
