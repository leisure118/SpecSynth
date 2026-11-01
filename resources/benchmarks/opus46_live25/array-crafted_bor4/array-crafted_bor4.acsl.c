#include<limits.h>

/*@ axiomatic BorRange {
    logic integer bor_range(int *x, integer lo, integer hi) reads x[lo .. hi-1];

    axiom bor_range_empty: \forall int *x, integer i;
      bor_range(x, i, i) == 0;

    axiom bor_range_step: \forall int *x, integer lo, integer hi;
      lo < hi ==> bor_range(x, lo, hi) == (bor_range(x, lo, hi-1) | (integer)x[hi-1]);

    axiom bor_range_split: \forall int *x, integer lo, integer mid, integer hi;
      lo <= mid <= hi ==>
      bor_range(x, lo, hi) == (bor_range(x, lo, mid) | bor_range(x, mid, hi));

    axiom or_comm: \forall integer a, b; (a | b) == (b | a);
    axiom or_assoc: \forall integer a, b, c; ((a | b) | c) == (a | (b | c));
    axiom or_zero: \forall integer a; (0 | a) == a;
    axiom or_idem: \forall integer a; (a | a) == a;

    axiom bor_range_bounds: \forall int *x, integer lo, integer hi;
      lo < hi ==> INT_MIN <= bor_range(x, lo, hi) <= INT_MAX;
}
*/

/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown(void);
#define N 100000
#define fun bor
#include <assert.h>

/*@
  requires \valid(x + (0 .. N-1));
  assigns \nothing;
  ensures (integer)\result == bor_range(x, 0, N);
*/
int bor (int x[N])
{
  int i;
  int res;
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
int main (void)
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
 L1: ;
  temp=x[0]; x[0] = x[1]; x[1] = temp;
  //@ assert bor_range(&x[0], 2, N) == \at(bor_range(&x[0], 2, N), L1);
  //@ assert bor_range(&x[0], 0, N) == (bor_range(&x[0], 0, 2) | bor_range(&x[0], 2, N));
  //@ assert bor_range(&x[0], 0, 2) == ((integer)x[0] | (integer)x[1]);
  //@ assert ((integer)x[0] | (integer)x[1]) == (\at((integer)x[0], L1) | \at((integer)x[1], L1));
  //@ assert \at(bor_range(&x[0], 0, 2), L1) == (\at((integer)x[0], L1) | \at((integer)x[1], L1));
  //@ assert \at(bor_range(&x[0], 0, N), L1) == (\at(bor_range(&x[0], 0, 2), L1) | \at(bor_range(&x[0], 2, N), L1));
  //@ assert bor_range(&x[0], 0, N) == \at(bor_range(&x[0], 0, N), L1);
  //@ assert (integer)ret == bor_range(&x[0], 0, N);
  ret2 = fun(x);
  temp=x[0];
 L2: ;
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer k; 0 <= k < i ==> x[k] == \at(x[k+1], L2);
    loop invariant \forall integer k; i <= k < N ==> x[k] == \at(x[k], L2);
    loop assigns i, x[0 .. N-2];
    loop variant N-1 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  //@ assert (integer)temp == \at((integer)x[0], L2);
  //@ assert \forall integer k; 0 <= k < N-1 ==> (integer)x[k] == \at((integer)x[k+1], L2);
  //@ assert (integer)x[N-1] == \at((integer)x[0], L2);
  //@ assert bor_range(&x[0], 0, N) == \at(bor_range(&x[0], 0, N), L2);
  //@ assert (integer)ret == bor_range(&x[0], 0, N);
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
