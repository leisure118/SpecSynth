#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 1000
#define fun bAnd
#include <assert.h>
/*@
  requires N >= 1;
  assigns \nothing;
  ensures \forall integer k; 0 <= k < N ==> (\result & x[k]) == \result;
*/
int bAnd (int x[N])
{
  int i;
  long long res;
  res = x[0];
/*@
  loop invariant 1 <= i <= N;
  loop invariant \forall integer k; 0 <= k < i ==> (res & x[k]) == res;
  loop invariant \forall integer k; 0 <= k < i ==> ((int)res & x[k]) == (int)res;
  loop assigns i, res;
  loop variant N - i;
*/
  for (i = 1; i < N; i++) {
/*@ assert (int)(res & x[i]) == ((int)res & x[i]); */
    res = res & x[i];
  }
  return res;
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
/*@ assert \forall integer k; 0 <= k < N ==> (ret & x[k]) == ret; */
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
/*@ assert \forall integer k; 0 <= k < N ==> (ret2 & x[k]) == ret2; */
  temp=x[0];
/*@
  loop invariant 0 <= i <= N-1;
  loop invariant \forall integer k; 0 <= k < i ==> x[k] == \at(x[k+1], LoopEntry);
  loop invariant \forall integer k; i < k < N ==> x[k] == \at(x[k], LoopEntry);
  loop assigns i, x[0 .. N-2];
  loop variant N-1-i;
*/
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
/*@ assert \forall integer k; 0 <= k < N ==> (ret5 & x[k]) == ret5; */
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
