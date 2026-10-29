/*@
  logic integer sum(int *arr, integer n) = (n <= 0) ? 0 : sum(arr, n-1) + arr[n-1];
*/
#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 5
#define fun avg
#include <assert.h>
/*@
  requires \valid(x+(0 .. N-1));
  requires \forall integer j; 0 <= j < N ==> INT_MIN <= x[j] < INT_MAX;
  assigns \nothing;
  ensures \result == sum(x, N) / N;
*/
int avg (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant ret == sum(x, i);
    loop assigns i, ret;
    loop variant N - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret + x[i];
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
    loop invariant \forall integer j; 0 <= j < i ==> INT_MIN <= x[j] < INT_MAX;
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
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], LoopEntry);
    loop invariant \forall integer j; i <= j < N ==> x[j] == \at(x[j], LoopEntry);
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
