#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100
#define fun bor
#include <assert.h>

/*@ axiomatic BorAll {
  logic integer bor_all(int *x, integer lo, integer hi) reads x[lo .. hi-1];

  axiom bor_empty: \forall int *x, integer lo;
    bor_all(x, lo, lo) == 0;

  axiom bor_right: \forall int *x, integer lo, integer hi;
    lo < hi ==> bor_all(x, lo, hi) == (bor_all(x, lo, hi-1) | (integer)x[hi-1]);

  axiom bor_left: \forall int *x, integer lo, integer hi;
    lo < hi ==> bor_all(x, lo, hi) == ((integer)x[lo] | bor_all(x, lo+1, hi));

  axiom bor_split: \forall int *x, integer lo, integer mid, integer hi;
    lo <= mid <= hi ==>
    bor_all(x, lo, hi) == (bor_all(x, lo, mid) | bor_all(x, mid, hi));

  axiom bor_or_comm: \forall integer a, integer b;
    (a | b) == (b | a);

  axiom bor_or_assoc: \forall integer a, integer b, integer c;
    ((a | b) | c) == (a | (b | c));

  axiom bor_or_zero: \forall integer a;
    (a | 0) == a;

  axiom bor_int_range: \forall int *x, integer lo, integer hi;
    lo < hi ==> -2147483648 <= bor_all(x, lo, hi) <= 2147483647;
}
*/

/*@
  requires \valid(x + (0 .. N-1));
  assigns \nothing;
  ensures (integer)\result == bor_all(x, 0, N);
*/
int bor (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant (integer)res == bor_all(x, 0, i);
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
  Pre_swap: ;
  temp=x[0];x[0] = x[1]; x[1] = temp;
  //@ assert bor_all(&x[0], 2, N) == \at(bor_all(&x[0], 2, N), Pre_swap);
  //@ assert \at(bor_all(&x[0], 0, N), Pre_swap) == ((integer)\at(x[0], Pre_swap) | (integer)\at(x[1], Pre_swap) | \at(bor_all(&x[0], 2, N), Pre_swap));
  //@ assert bor_all(&x[0], 0, N) == ((integer)x[0] | (integer)x[1] | bor_all(&x[0], 2, N));
  //@ assert (integer)x[0] == (integer)\at(x[1], Pre_swap);
  //@ assert (integer)x[1] == (integer)\at(x[0], Pre_swap);
  //@ assert ((integer)x[0] | (integer)x[1]) == ((integer)\at(x[0], Pre_swap) | (integer)\at(x[1], Pre_swap));
  //@ assert bor_all(&x[0], 0, N) == \at(bor_all(&x[0], 0, N), Pre_swap);
  //@ assert (integer)ret == bor_all(&x[0], 0, N);
  ret2 = fun(x);
  //@ assert ret == ret2;
  Pre_rotate: ;
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; 0 <= j < i ==> (integer)x[j] == (integer)\at(x[j+1], Pre_rotate);
    loop invariant \forall integer j; i <= j < N ==> (integer)x[j] == (integer)\at(x[j], Pre_rotate);
    loop invariant \let ci = i; bor_all(&x[0], 0, ci) == \at(bor_all(&x[0], 1, ci+1), Pre_rotate);
    loop assigns i, x[0 .. N-2];
    loop variant N-1-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  //@ assert bor_all(&x[0], 0, N-1) == \at(bor_all(&x[0], 1, N), Pre_rotate);
  x[N-1] = temp;
  //@ assert (integer)x[N-1] == (integer)\at(x[0], Pre_rotate);
  //@ assert bor_all(&x[0], 0, N) == (bor_all(&x[0], 0, N-1) | (integer)x[N-1]);
  //@ assert bor_all(&x[0], 0, N) == (\at(bor_all(&x[0], 1, N), Pre_rotate) | (integer)\at(x[0], Pre_rotate));
  //@ assert (\at(bor_all(&x[0], 1, N), Pre_rotate) | (integer)\at(x[0], Pre_rotate)) == ((integer)\at(x[0], Pre_rotate) | \at(bor_all(&x[0], 1, N), Pre_rotate));
  //@ assert ((integer)\at(x[0], Pre_rotate) | \at(bor_all(&x[0], 1, N), Pre_rotate)) == \at(bor_all(&x[0], 0, N), Pre_rotate);
  //@ assert bor_all(&x[0], 0, N) == \at(bor_all(&x[0], 0, N), Pre_rotate);
  //@ assert (integer)ret == bor_all(&x[0], 0, N);
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
