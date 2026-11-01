#include<limits.h>

/*@ axiomatic BorFold {
    logic integer bor_range{L}(int *a, integer lo, integer hi) reads a[lo .. (hi-1)];

    axiom bor_empty: \forall int *a, integer lo;
      bor_range(a, lo, lo) == 0;

    axiom bor_base: \forall int *a, integer i;
      bor_range(a, i, i+1) == (integer)a[i];

    axiom bor_step: \forall int *a, integer lo, integer hi;
      lo < hi - 1 ==>
      bor_range(a, lo, hi) == (bor_range(a, lo, hi-1) | (integer)a[hi-1]);

    axiom bor_left: \forall int *a, integer lo, integer hi;
      lo < hi - 1 ==>
      bor_range(a, lo, hi) == ((integer)a[lo] | bor_range(a, lo+1, hi));

    axiom bor_range_bounded: \forall int *a, integer lo, hi;
      lo < hi ==> -2147483648 <= bor_range(a, lo, hi) <= 2147483647;

    axiom bor_frame{L1, L2}: \forall int *a, integer lo, hi;
      (\forall integer k; lo <= k < hi ==> \at(a[k], L1) == \at(a[k], L2)) ==>
      \at(bor_range(a, lo, hi), L1) == \at(bor_range(a, lo, hi), L2);
}
*/

/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 1000
#define fun bor
#include <assert.h>

/*@
  requires \valid_read(x + (0 .. N-1));
  assigns \nothing;
  ensures (integer)\result == bor_range(x, 0, N);
*/
int bor (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant (integer)res == bor_range(x, 0, i);
    loop assigns i, res;
    loop variant N - i;
  */
  for (i = 1; i < N; i++) {
    res = res | x[i];
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
  L_swap: ;
  temp=x[0];x[0] = x[1]; x[1] = temp;
  //@ assert bor_range(&x[0], 0, N) == ((integer)x[0] | bor_range(&x[0], 1, N));
  //@ assert bor_range(&x[0], 1, N) == ((integer)x[1] | bor_range(&x[0], 2, N));
  //@ assert bor_range(&x[0], 2, N) == \at(bor_range(&x[0], 2, N), L_swap);
  //@ assert (integer)x[0] == \at((integer)x[1], L_swap);
  //@ assert (integer)x[1] == \at((integer)x[0], L_swap);
  //@ assert \at(bor_range(&x[0], 0, N), L_swap) == (\at((integer)x[0], L_swap) | \at(bor_range(&x[0], 1, N), L_swap));
  //@ assert \at(bor_range(&x[0], 1, N), L_swap) == (\at((integer)x[1], L_swap) | \at(bor_range(&x[0], 2, N), L_swap));
  //@ assert bor_range(&x[0], 0, N) == \at(bor_range(&x[0], 0, N), L_swap);
  ret2 = fun(x);
  //@ assert (integer)ret == \at(bor_range(&x[0], 0, N), L_swap);
  //@ assert (integer)ret2 == bor_range(&x[0], 0, N);
  //@ assert ret == ret2;
  L_rot: ;
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant (integer)temp == \at((integer)x[0], L_rot);
    loop invariant \forall integer j; i <= j < N ==> (integer)x[j] == \at((integer)x[j], L_rot);
    loop invariant \let k = (integer)i; bor_range(&x[0], 0, k) == \at(bor_range(&x[0], 1, k+1), L_rot);
    loop assigns i, x[0 .. N-2];
    loop variant N-1 - i;
  */
  for(int i =0 ; i<N-1; i++){
     L_body: ;
     x[i] = x[i+1];
     //@ assert \let k = (integer)i; \forall integer j; 0 <= j < k ==> (integer)x[j] == \at((integer)x[j], L_body);
     //@ assert \let k = (integer)i; bor_range(&x[0], 0, k) == \at(bor_range(&x[0], 0, k), L_body);
     //@ assert \let k = (integer)i; bor_range(&x[0], 0, k+1) == (bor_range(&x[0], 0, k) | (integer)x[k]);
     //@ assert \let k = (integer)i; \at(bor_range(&x[0], 1, k+2), L_rot) == (\at(bor_range(&x[0], 1, k+1), L_rot) | \at((integer)x[k+1], L_rot));
  }
  //@ assert bor_range(&x[0], 0, N-1) == \at(bor_range(&x[0], 1, N), L_rot);
  x[N-1] = temp;
  //@ assert (integer)x[N-1] == \at((integer)x[0], L_rot);
  //@ assert bor_range(&x[0], 0, N) == (bor_range(&x[0], 0, N-1) | (integer)x[N-1]);
  //@ assert bor_range(&x[0], 0, N) == (\at(bor_range(&x[0], 1, N), L_rot) | \at((integer)x[0], L_rot));
  //@ assert \at(bor_range(&x[0], 0, N), L_rot) == (\at((integer)x[0], L_rot) | \at(bor_range(&x[0], 1, N), L_rot));
  //@ assert bor_range(&x[0], 0, N) == \at(bor_range(&x[0], 0, N), L_rot);
  ret5 = fun(x);
  //@ assert (integer)ret2 == \at(bor_range(&x[0], 0, N), L_rot);
  //@ assert (integer)ret5 == bor_range(&x[0], 0, N);
  //@ assert ret == ret5;
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
