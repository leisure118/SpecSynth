#include<limits.h>

/*@ axiomatic BAnd {
  logic integer band_range{L}(int *x, integer lo, integer hi) reads x[lo .. hi-1];

  axiom band_base{L}: \forall int *x, integer i;
    band_range(x, i, i+1) == x[i];

  axiom band_step{L}: \forall int *x, integer lo, integer hi;
    lo + 1 < hi ==>
    band_range(x, lo, hi) == (band_range(x, lo, hi-1) & x[hi-1]);

  axiom band_bounds{L}: \forall int *x, integer lo, integer hi;
    lo < hi ==> INT_MIN <= band_range(x, lo, hi) <= INT_MAX;

  axiom band_swap{L1, L2}: \forall int *x, integer n;
    n >= 2 ==>
    \at(x[0], L2) == \at(x[1], L1) ==>
    \at(x[1], L2) == \at(x[0], L1) ==>
    (\forall integer k; 2 <= k < n ==> \at(x[k], L2) == \at(x[k], L1)) ==>
    band_range{L2}(x, 0, n) == band_range{L1}(x, 0, n);

  axiom band_rotate_left{L1, L2}: \forall int *x, integer n;
    n >= 1 ==>
    (\forall integer k; 0 <= k < n-1 ==> \at(x[k], L2) == \at(x[k+1], L1)) ==>
    \at(x[n-1], L2) == \at(x[0], L1) ==>
    band_range{L2}(x, 0, n) == band_range{L1}(x, 0, n);
}
*/

/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define fun bAnd
#include <assert.h>
int N;

/*@
  requires N >= 1;
  requires \valid(x+(0 .. N-1));
  assigns \nothing;
  ensures \result == (int)band_range(x, 0, N);
*/
int bAnd (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant res == band_range(x, 0, i);
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
    //@ admit \valid(x+(0 .. N-1));
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
    //@ assert ret == (int)band_range(x, 0, N);
  L_before_swap: ;
    temp=x[0];x[0] = x[1]; x[1] = temp;
    //@ assert x[0] == \at(x[1], L_before_swap);
    //@ assert x[1] == \at(x[0], L_before_swap);
    //@ assert \forall integer k; 2 <= k < N ==> x[k] == \at(x[k], L_before_swap);
    //@ assert band_range(x, 0, N) == band_range{L_before_swap}(x, 0, N);
    //@ assert (int)band_range(x, 0, N) == ret;
    ret2 = fun(x);
    //@ assert ret2 == (int)band_range(x, 0, N);
    //@ assert ret2 == ret;
  L_before_rot: ;
    temp=x[0];
    //@ assert temp == \at(x[0], L_before_rot);
    /*@
      loop invariant 0 <= i <= N-1;
      loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], L_before_rot);
      loop invariant \forall integer j; i <= j < N ==> x[j] == \at(x[j], L_before_rot);
      loop assigns i, x[0 .. N-2];
      loop variant N-1-i;
    */
    for(int i =0 ; i<N-1; i++){
       x[i] = x[i+1];
    }
    x[N-1] = temp;
    //@ assert \forall integer k; 0 <= k < N-1 ==> x[k] == \at(x[k+1], L_before_rot);
    //@ assert x[N-1] == \at(x[0], L_before_rot);
    //@ assert band_range(x, 0, N) == band_range{L_before_rot}(x, 0, N);
    //@ assert (int)band_range(x, 0, N) == ret;
    ret5 = fun(x);
    //@ assert ret5 == (int)band_range(x, 0, N);
    //@ assert ret5 == ret;
    //@ assert !(ret != ret2 || ret !=ret5);
  }
  return 1;
}
