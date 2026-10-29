#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
/*@ axiomatic Mapsum {
  @   logic integer mapsum_val(int *a, integer n) =
  @     n <= 0 ? 0 : mapsum_val(a, n-1) + (n-1) + a[n-1];
  @ }
  @*/
#define N 1000
#define fun mapsum
#include <assert.h>
/*@
  requires \valid(x + (0 .. N-1));
  assigns \nothing;
*/
int mapsum (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant ret == \at(ret, LoopEntry) + mapsum_val(x, i);
    loop assigns i, ret;
    loop variant N - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret+ i + x[i];
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
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], LoopEntry);
    loop invariant \forall integer j; i <= j < N ==> x[j] == \at(x[j], LoopEntry);
    loop assigns i, x[0 .. N-2];
    loop variant (N-1) - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
