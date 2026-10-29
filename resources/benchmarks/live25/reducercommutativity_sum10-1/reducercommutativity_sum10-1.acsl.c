#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 10
#define fun sum
#include <assert.h>

/*@
  axiomatic Sum {
    logic integer sum(int *a, integer n) =
      n <= 0 ? 0 : sum(a, n-1) + a[n-1];
  }
*/

/*@
  requires \valid(x + (0 .. N-1));
  ensures \result == (int)sum(x, N);
  assigns \nothing;
*/
int sum (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant (integer)ret == sum(x, i);
    loop assigns i, ret;
    loop variant N - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret + x[i];
  }
  return ret;
}
int main ()
{
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
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  temp=x[0];
  //@ ghost int old0 = x[0], old1 = x[1], old2 = x[2], old3 = x[3], old4 = x[4];
  //@ ghost int old5 = x[5], old6 = x[6], old7 = x[7], old8 = x[8], old9 = x[9];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] ==
      (j==0?old1:(j==1?old2:(j==2?old3:(j==3?old4:(j==4?old5:
      (j==5?old6:(j==6?old7:(j==7?old8:old9))))))));
    loop invariant \forall integer j; i <= j < N ==> x[j] ==
      (j==0?old0:(j==1?old1:(j==2?old2:(j==3?old3:(j==4?old4:
      (j==5?old5:(j==6?old6:(j==7?old7:(j==8?old8:old9)))))))));
    loop assigns i, x[0 .. N-2];
    loop variant N-1 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
