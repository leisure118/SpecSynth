#include<limits.h>

/*@ axiomatic SumRange {
      logic integer sum_range(int *a, integer lo, integer hi) reads a[lo .. hi-1];
      axiom sum_empty: \forall int *a, integer lo, hi; lo >= hi ==> sum_range(a, lo, hi) == 0;
      axiom sum_one: \forall int *a, integer i; sum_range(a, i, i+1) == (integer)a[i];
      axiom sum_split: \forall int *a, integer lo, mid, hi;
        lo <= mid <= hi ==> sum_range(a, lo, hi) == sum_range(a, lo, mid) + sum_range(a, mid, hi);
    }
*/

/*@ axiomatic SumRangePermut {
      axiom frame_2_N{L1,L2}: \forall int *a;
        (\forall integer k; 2 <= k < 100000 ==> \at(a[k], L1) == \at(a[k], L2)) ==>
        \at(sum_range(a, 2, 100000), L1) == \at(sum_range(a, 2, 100000), L2);
      axiom swap_01{L1,L2}: \forall int *a;
        \at(a[0], L1) == \at(a[1], L2) ==>
        \at(a[1], L1) == \at(a[0], L2) ==>
        (\forall integer k; 2 <= k < 100000 ==> \at(a[k], L1) == \at(a[k], L2)) ==>
        \at(sum_range(a, 0, 100000), L1) == \at(sum_range(a, 0, 100000), L2);
      axiom rotate_left{L1,L2}: \forall int *a;
        (\forall integer k; 0 <= k < 99999 ==> \at(a[k], L1) == \at(a[k+1], L2)) ==>
        \at(a[99999], L1) == \at(a[0], L2) ==>
        \at(sum_range(a, 0, 100000), L1) == \at(sum_range(a, 0, 100000), L2);
    }
*/

/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100000
#define fun mapsum
#include <assert.h>

/*@ requires \valid(x+(0 .. N-1));
    requires \forall integer i; 0 <= i < N ==> INT_MIN <= (integer)x[i] <= INT_MAX - 1;
    assigns \nothing;
    ensures \result == (int)(sum_range(x, 0, N) + (N*(N-1))/2);
*/
int mapsum (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@ loop invariant 0 <= i <= N;
      loop invariant ret == sum_range(x, 0, i) + (i*(i-1))/2;
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
  /*@ loop invariant 0 <= i <= N;
      loop invariant \forall integer j; 0 <= j < i ==> INT_MIN <= (integer)x[j] < INT_MAX;
      loop assigns i, x[0 .. N-1];
      loop variant N - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  L_swap:
  temp=x[0];x[0] = x[1]; x[1] = temp;
  /*@ assert x[0] == \at(x[1], L_swap); */
  /*@ assert x[1] == \at(x[0], L_swap); */
  /*@ assert \forall integer k; 2 <= k < N ==> x[k] == \at(x[k], L_swap); */
  /*@ assert sum_range{Here}(&x[0], 0, N) == sum_range{L_swap}(&x[0], 0, N); */
  /*@ assert \forall integer j; 0 <= j < N ==> INT_MIN <= (integer)x[j] < INT_MAX; */
  ret2 = fun(x);
  /*@ assert ret == ret2; */
  L_rot:
  temp=x[0];
  /*@ loop invariant 0 <= i <= N-1;
      loop invariant temp == \at(x[0], L_rot);
      loop invariant \forall integer k; 0 <= k < i ==> x[k] == \at(x[k+1], L_rot);
      loop invariant \forall integer k; i <= k < N ==> x[k] == \at(x[k], L_rot);
      loop assigns i, x[0 .. N-2];
      loop variant N - 1 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  /*@ assert \forall integer k; 0 <= k < N-1 ==> x[k] == \at(x[k+1], L_rot); */
  /*@ assert x[N-1] == \at(x[0], L_rot); */
  /*@ assert sum_range{Here}(&x[0], 0, N) == sum_range{L_rot}(&x[0], 0, N); */
  /*@ assert \forall integer j; 0 <= j < N ==> INT_MIN <= (integer)x[j] < INT_MAX; */
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
