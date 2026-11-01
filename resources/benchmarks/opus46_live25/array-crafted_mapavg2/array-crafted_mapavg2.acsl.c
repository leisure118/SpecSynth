#include<limits.h>

/*@ axiomatic ArraySum {
    logic integer array_sum(int *a, integer lo, integer hi) reads a[lo .. hi-1];

    axiom sum_empty: \forall int *a, integer lo, hi;
      hi <= lo ==> array_sum(a, lo, hi) == 0;

    axiom sum_next: \forall int *a, integer lo, hi;
      lo < hi ==> array_sum(a, lo, hi) == array_sum(a, lo, hi-1) + a[hi-1];

    axiom sum_first: \forall int *a, integer lo, hi;
      lo < hi ==> array_sum(a, lo, hi) == a[lo] + array_sum(a, lo+1, hi);

    axiom sum_one: \forall int *a, integer k;
      array_sum(a, k, k+1) == a[k];

    axiom sum_bounded_upper: \forall int *a, integer lo, hi, integer B;
      lo <= hi ==>
      (\forall integer k; lo <= k < hi ==> a[k] <= B) ==>
      array_sum(a, lo, hi) <= (hi - lo) * B;

    axiom sum_bounded_lower: \forall int *a, integer lo, hi, integer B;
      lo <= hi ==>
      (\forall integer k; lo <= k < hi ==> B <= a[k]) ==>
      (hi - lo) * B <= array_sum(a, lo, hi);
    }
*/

/*@
  assigns \nothing;
  ensures -1000000 <= \result <= 1000000;
*/
int unknown();
#define N 1000
#define fun mapavg
#include <assert.h>

/*@
  requires \valid_read(x+(0 .. N-1));
  requires \forall integer k; 0 <= k < N ==> -1000000 <= x[k] <= 1000000;
  assigns \nothing;
  ensures \result == (N*(N-1)/2 + array_sum(x, 0, N)) / N;
*/
int mapavg (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant ret == i*(i-1)/2 + array_sum(x, 0, i);
    loop assigns i, ret;
    loop variant N - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret+ i + x[i];
  }
  //@ assert -1000000000 <= array_sum(x, 0, N) <= 1000000000;
  //@ assert -1000499 <= (N*(N-1)/2 + array_sum(x, 0, N)) / N <= 1000499;
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
    loop invariant \forall integer j; 0 <= j < i ==> -1000000 <= x[j] <= 1000000;
    loop assigns i, x[0 .. N-1];
    loop variant N - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  L1: ;
  temp=x[0];
  x[0] = x[1];
  x[1] = temp;
  //@ assert \forall integer j; 0 <= j < N ==> -1000000 <= x[j] <= 1000000;
  //@ assert x[0] + x[1] == \at(x[0], L1) + \at(x[1], L1);
  //@ assert array_sum(&x[0], 0, N) == \at(array_sum(&x[0], 0, N), L1);
  ret2 = fun(x);
  //@ assert ret == ret2;
  L2: ;
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; i <= j < N ==> x[j] == \at(x[j], L2);
    loop invariant \forall integer j; 0 <= j < N ==> -1000000 <= x[j] <= 1000000;
    loop invariant array_sum(&x[0], 0, N) == \at(array_sum(&x[0], 1, N), L2) + x[i];
    loop assigns i, x[0 .. N-2];
    loop variant N-1 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  //@ assert x[N-1] == \at(x[N-1], L2);
  x[N-1] = temp;
  //@ assert x[N-1] == \at(x[0], L2);
  //@ assert \forall integer j; 0 <= j < N ==> -1000000 <= x[j] <= 1000000;
  //@ assert array_sum(&x[0], 0, N) == \at(array_sum(&x[0], 1, N), L2) + x[N-1];
  //@ assert \at(array_sum(&x[0], 0, N), L2) == \at(x[0], L2) + \at(array_sum(&x[0], 1, N), L2);
  //@ assert array_sum(&x[0], 0, N) == \at(array_sum(&x[0], 0, N), L2);
  ret5 = fun(x);
  //@ assert ret2 == ret5;
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
