#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 10000
#define fun xor
#include <assert.h>

/*@ axiomatic XorFold {
  logic integer xor_fold{L}(int *x, integer lo, integer hi)
    reads x[lo .. hi-1];

  axiom xor_fold_empty{L}:
    \forall int *x, integer lo, hi;
    hi <= lo ==> xor_fold{L}(x, lo, hi) == 0;

  axiom xor_fold_right{L}:
    \forall int *x, integer lo, hi;
    lo < hi ==> xor_fold{L}(x, lo, hi) == (xor_fold{L}(x, lo, hi-1) ^ (integer)x[hi-1]);

  axiom xor_zero_left:
    \forall integer a; (0 ^ a) == a;

  axiom xor_zero_right:
    \forall integer a; (a ^ 0) == a;

  axiom xor_comm:
    \forall integer a, b; (a ^ b) == (b ^ a);

  axiom xor_assoc:
    \forall integer a, b, c; ((a ^ b) ^ c) == (a ^ (b ^ c));

  axiom xor_self_cancel:
    \forall integer a; (a ^ a) == 0;

  axiom xor_int_range:
    \forall integer a, b;
    INT_MIN <= a <= INT_MAX ==> INT_MIN <= b <= INT_MAX ==>
    INT_MIN <= (a ^ b) <= INT_MAX;

  axiom xor_fold_swap{L1, L2}:
    \forall int *x, integer n, i, j;
    0 <= i < n ==> 0 <= j < n ==> i != j ==>
    \at(x[i], L2) == \at(x[j], L1) ==>
    \at(x[j], L2) == \at(x[i], L1) ==>
    (\forall integer k; 0 <= k < n ==> k != i ==> k != j ==>
      \at(x[k], L2) == \at(x[k], L1)) ==>
    xor_fold{L2}(x, 0, n) == xor_fold{L1}(x, 0, n);

  axiom xor_fold_rotation{L1, L2}:
    \forall int *x, integer n;
    n > 0 ==>
    \at(x[n-1], L2) == \at(x[0], L1) ==>
    (\forall integer k; 0 <= k < n-1 ==> \at(x[k], L2) == \at(x[k+1], L1)) ==>
    xor_fold{L2}(x, 0, n) == xor_fold{L1}(x, 0, n);
}
*/

/*@
  requires \valid(x + (0 .. N-1));
  assigns \nothing;
  ensures \result == xor_fold(x, 0, N);
*/
int xor (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant res == xor_fold(x, 0, i);
    loop invariant INT_MIN <= res <= INT_MAX;
    loop assigns i, res;
    loop variant N - i;
  */
  for (i = 1; i < N; i++) {
    res = res ^ x[i];
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
  BeforeSwap: ;
  temp=x[0];x[0] = x[1]; x[1] = temp;
  /*@ assert x[0] == \at(x[1], BeforeSwap); */
  /*@ assert x[1] == \at(x[0], BeforeSwap); */
  /*@ assert \forall integer k; 0 <= k < N ==> k != 0 ==> k != 1 ==> x[k] == \at(x[k], BeforeSwap); */
  /*@ assert xor_fold(&x[0], 0, N) == xor_fold{BeforeSwap}(&x[0], 0, N); */
  ret2 = fun(x);
  temp=x[0];
  BeforeShift: ;
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], BeforeShift);
    loop invariant \forall integer j; i <= j < N ==> x[j] == \at(x[j], BeforeShift);
    loop assigns i, x[0 .. N-2];
    loop variant N-1-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  /*@ assert x[N-1] == \at(x[0], BeforeShift); */
  /*@ assert \forall integer k; 0 <= k < N-1 ==> x[k] == \at(x[k+1], BeforeShift); */
  /*@ assert xor_fold(&x[0], 0, N) == xor_fold{BeforeShift}(&x[0], 0, N); */
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
