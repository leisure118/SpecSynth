#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100
#define fun mapavg
#include <assert.h>
/*@
logic integer sum_part(int *a, integer n) =
  n <= 0 ? 0 : sum_part(a, n-1) + (n-1 + a[n-1]);
*/

/*@
  requires \valid_read(x + (0 .. N-1));
  assigns \nothing;
  ensures \result == (int)(sum_part(x, N) / N);
*/
int mapavg (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant ret == sum_part(x, i);
    loop assigns i, ret;
    loop variant N - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret+ i + x[i];
  }
  return ret / N;
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
  L_after_fun1: ;
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  L_after_swap: ;
  //@ admit sum_part{L_after_fun1}((int *)x, N) == sum_part{L_after_swap}((int *)x, N);
  ret2 = fun(x);
  temp=x[0];
  L_before_rotate: ;
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], LoopEntry);
    loop invariant \forall integer j; i <= j < N-1 ==> x[j] == \at(x[j], LoopEntry);
    loop invariant x[N-1] == \at(x[N-1], LoopEntry);
    loop assigns i, x[0 .. N-2];
    loop variant N-1 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  L_after_rotate: ;
  //@ admit sum_part{L_before_rotate}((int *)x, N) == sum_part{L_after_rotate}((int *)x, N);
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
