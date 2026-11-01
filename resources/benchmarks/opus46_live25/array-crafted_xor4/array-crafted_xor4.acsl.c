#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100000
#define fun xor

/*@ axiomatic XorFold {
  logic integer xor_fold{L}(int *x, integer lo, integer hi) reads x[lo .. hi-1];

  axiom xor_base{L}:
    \forall int *x, integer lo; xor_fold{L}(x, lo, lo) == 0;

  axiom xor_one{L}:
    \forall int *x, integer lo; xor_fold{L}(x, lo, lo+1) == (integer)x[lo];

  axiom xor_step{L}:
    \forall int *x, integer lo, integer hi; lo < hi ==>
      xor_fold{L}(x, lo, hi) == (xor_fold{L}(x, lo, hi-1) ^ (integer)x[hi-1]);

  axiom xor_two{L}:
    \forall int *x, integer lo;
      xor_fold{L}(x, lo, lo+2) == ((integer)x[lo] ^ (integer)x[lo+1]);

  axiom xor_comm:
    \forall integer a, b; (a ^ b) == (b ^ a);

  axiom xor_zero:
    \forall integer a; (a ^ 0) == a;

  axiom xor_split{L}:
    \forall int *x, integer lo, integer mid, integer hi; lo <= mid <= hi ==>
      xor_fold{L}(x, lo, hi) == (xor_fold{L}(x, lo, mid) ^ xor_fold{L}(x, mid, hi));

  axiom xor_split_at2{L}:
    \forall int *x; xor_fold{L}(x, 0, N) == (xor_fold{L}(x, 0, 2) ^ xor_fold{L}(x, 2, N));

  axiom xor_split_at1{L}:
    \forall int *x; xor_fold{L}(x, 0, N) == (xor_fold{L}(x, 0, 1) ^ xor_fold{L}(x, 1, N));

  axiom xor_one_at0{L}:
    \forall int *x; xor_fold{L}(x, 0, 1) == (integer)x[0];

  axiom xor_step_0_N{L}:
    \forall int *x; xor_fold{L}(x, 0, N) == (xor_fold{L}(x, 0, N-1) ^ (integer)x[N-1]);

  axiom xor_frame{L1, L2}:
    \forall int *x, integer lo, integer hi;
      (\forall integer k; lo <= k < hi ==> \at(x[k], L1) == \at(x[k], L2)) ==>
      xor_fold{L1}(x, lo, hi) == xor_fold{L2}(x, lo, hi);

  axiom xor_reindex{L1, L2}:
    \forall int *x, integer lo1, integer lo2, integer n;
      n >= 0 ==>
      (\forall integer k; 0 <= k < n ==> \at(x[lo1 + k], L1) == \at(x[lo2 + k], L2)) ==>
      xor_fold{L1}(x, lo1, lo1 + n) == xor_fold{L2}(x, lo2, lo2 + n);
}
*/

#include <assert.h>

/*@
  requires \valid(x + (0 .. N-1));
  assigns \nothing;
  ensures \result == (int)(xor_fold(x, 0, N));
*/
int xor (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant res == xor_fold(x, 0, i);
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
  S1: ;
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  S2: ;
  //@ assert \at(x[0], S2) == \at(x[1], S1);
  //@ assert \at(x[1], S2) == \at(x[0], S1);
  //@ assert \forall integer k; 2 <= k < N ==> \at(x[k], S2) == \at(x[k], S1);
  //@ assert xor_fold{S2}(&x[0], 2, N) == xor_fold{S1}(&x[0], 2, N);
  //@ assert xor_fold{S1}(&x[0], 0, 2) == ((integer)\at(x[0], S1) ^ (integer)\at(x[1], S1));
  //@ assert xor_fold{S2}(&x[0], 0, 2) == ((integer)\at(x[0], S2) ^ (integer)\at(x[1], S2));
  //@ assert xor_fold{S2}(&x[0], 0, 2) == ((integer)\at(x[1], S1) ^ (integer)\at(x[0], S1));
  //@ assert ((integer)\at(x[1], S1) ^ (integer)\at(x[0], S1)) == ((integer)\at(x[0], S1) ^ (integer)\at(x[1], S1));
  //@ assert xor_fold{S2}(&x[0], 0, 2) == xor_fold{S1}(&x[0], 0, 2);
  //@ assert xor_fold{S1}(&x[0], 0, N) == (xor_fold{S1}(&x[0], 0, 2) ^ xor_fold{S1}(&x[0], 2, N));
  //@ assert xor_fold{S2}(&x[0], 0, N) == (xor_fold{S2}(&x[0], 0, 2) ^ xor_fold{S2}(&x[0], 2, N));
  //@ assert xor_fold{S2}(&x[0], 0, N) == xor_fold{S1}(&x[0], 0, N);
  //@ assert ret == (int)(xor_fold{S1}(&x[0], 0, N));
  //@ assert xor_fold{S2}(&x[0], 0, N) == (xor_fold{S2}(&x[0], 0, 1) ^ xor_fold{S2}(&x[0], 1, N));
  //@ assert xor_fold{S2}(&x[0], 0, 1) == (integer)\at(x[0], S2);
  //@ assert xor_fold{S2}(&x[0], 0, N) == ((integer)\at(x[0], S2) ^ xor_fold{S2}(&x[0], 1, N));
  ret2 = fun(x);
  //@ assert ret2 == (int)(xor_fold{S2}(&x[0], 0, N));
  //@ assert ret == ret2;
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer k; 0 <= k < i ==> x[k] == \at(x[k+1], S2);
    loop invariant \forall integer k; i <= k < N ==> x[k] == \at(x[k], S2);
    loop assigns i, x[0 .. N-2];
    loop variant N-1-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  S3: ;
  //@ assert \forall integer k; 0 <= k < N-1 ==> \at(x[k], S3) == \at(x[k+1], S2);
  //@ assert \at(x[N-1], S3) == \at(x[0], S2);
  //@ assert xor_fold{S3}(&x[0], 0, N-1) == xor_fold{S2}(&x[0], 1, N);
  //@ assert xor_fold{S3}(&x[0], 0, N) == (xor_fold{S3}(&x[0], 0, N-1) ^ (integer)\at(x[N-1], S3));
  //@ assert xor_fold{S3}(&x[0], 0, N) == (xor_fold{S2}(&x[0], 1, N) ^ (integer)\at(x[0], S2));
  //@ assert (xor_fold{S2}(&x[0], 1, N) ^ (integer)\at(x[0], S2)) == ((integer)\at(x[0], S2) ^ xor_fold{S2}(&x[0], 1, N));
  //@ assert xor_fold{S3}(&x[0], 0, N) == xor_fold{S2}(&x[0], 0, N);
  ret5 = fun(x);
  //@ assert ret5 == (int)(xor_fold{S3}(&x[0], 0, N));
  //@ assert ret == ret5;
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
