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
logic integer band_of(int *x, integer n) =
  n == 0 ? x[0] : (band_of(x, n-1) & x[n]);
*/
int bAnd (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
  loop invariant 1 <= i <= N;
  loop invariant res == band_of(x, i-1);
  loop assigns res, i;
  loop variant N - i;
  */
  for (i = 1; i < N; i++) {
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
  loop assigns x[0..N-1], i;
  loop variant N - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  //@ label shift_start;
  temp=x[0];
  /*@
  loop invariant 0 <= i <= N-1;
  loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], shift_start);
  loop invariant \forall integer j; i <= j < N-1 ==> x[j] == \at(x[j], shift_start);
  loop invariant x[N-1] == \at(x[N-1], shift_start);
  loop assigns x[0..N-2], i;
  loop variant N - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  //@ assert \forall integer j; 0 <= j < N-1 ==> x[j] == \at(x[j+1], shift_start);
  //@ assert x[N-1] == \at(x[0], shift_start);
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
