#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 5
#define fun max
#include <assert.h>
/*@
  logic integer max_array{L}(int *a, integer n) =
    n <= 0 ? 0 :
    (max_array(a, n-1) > a[n-1] ? max_array(a, n-1) : a[n-1]);
*/
/*@
  requires \valid(x + (0 .. N-1));
  assigns \nothing;
  ensures \result >= 0;
  ensures \result == max_array(x, N);
*/
int max (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant ret == max_array(x, i);
    loop assigns i, ret;
    loop variant N - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret < x[i] ? x[i] : ret;
  }
  //@ admit 0 <= ret <= 2147483647;
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
  /*@
    loop invariant 0 <= i <= N-1;
    loop assigns i, x[0 .. N-2];
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], LoopEntry);
    loop invariant \forall integer j; i <= j < N ==> x[j] == \at(x[j], LoopEntry);
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
