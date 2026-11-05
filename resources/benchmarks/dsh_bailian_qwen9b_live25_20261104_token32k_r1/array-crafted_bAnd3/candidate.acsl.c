#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 10000
#define fun bAnd
#include <assert.h>
/*@
  requires \valid_read(x + (0 .. N-1));
  assigns \nothing;
  ensures \forall integer j; 0 <= j < N ==> \result == (\result & x[j]);
  ensures \forall integer v; (\forall integer j; 0 <= j < N ==> (v & x[j]) == v) ==> (v & \result) == v;
*/
int bAnd (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant INT_MIN <= res <= INT_MAX;
    loop invariant \forall integer j; 0 <= j < i ==> res == (res & x[j]);
    loop invariant \forall integer v; (\forall integer j; 0 <= j < i ==> (v & x[j]) == v) ==> (v & res) == v;
    loop assigns i, res;
    loop variant N - i;
  */
  for (i = 1; i < N; i++) {
    res = res & x[i];
  }
  return res;
}
/*@
  assigns \nothing;
*/
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
  //@ assert ret == ret2;
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \old(x[j+1]);
    loop invariant \forall integer j; i <= j < N ==> x[j] == \old(x[j]);
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
