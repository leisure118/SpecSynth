#include<limits.h>

/*@ axiomatic BandAll {
    logic integer band_all{L}(int *x, integer n) reads x[0 .. n-1];

    axiom band_base{L}: \forall int *x;
      band_all{L}(x, 1) == x[0];

    axiom band_ind{L}: \forall int *x, integer n; n >= 2 ==>
      band_all{L}(x, n) == (band_all{L}(x, n-1) & x[n-1]);

    axiom band_all_int_range{L}: \forall int *x, integer n; n >= 1 ==>
      INT_MIN <= band_all{L}(x, n) <= INT_MAX;

    axiom band_swap_01{L1, L2}: \forall int *x, integer n;
      n >= 2 ==>
      \at(x[0], L2) == \at(x[1], L1) ==>
      \at(x[1], L2) == \at(x[0], L1) ==>
      (\forall integer k; 2 <= k < n ==> \at(x[k], L2) == \at(x[k], L1)) ==>
      band_all{L2}(x, n) == band_all{L1}(x, n);

    axiom band_rotate_left{L1, L2}: \forall int *x, integer n;
      n >= 2 ==>
      \at(x[n-1], L2) == \at(x[0], L1) ==>
      (\forall integer k; 0 <= k < n-1 ==> \at(x[k], L2) == \at(x[k+1], L1)) ==>
      band_all{L2}(x, n) == band_all{L1}(x, n);
  }
*/

/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100
#define fun bAnd
#include <assert.h>

/*@
  requires \valid_read(x + (0 .. N-1));
  assigns \nothing;
  ensures \result == (int)band_all(x, N);
*/
int bAnd (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant res == band_all(x, i);
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
  //@ assert ret == (int)band_all(&x[0], N);
 PreSwap: ;
  temp=x[0];x[0] = x[1]; x[1] = temp;
  //@ assert x[0] == \at(x[1], PreSwap);
  //@ assert x[1] == \at(x[0], PreSwap);
  //@ assert \forall integer k; 2 <= k < N ==> x[k] == \at(x[k], PreSwap);
  //@ assert band_all(&x[0], N) == \at(band_all(&x[0], N), PreSwap);
  ret2 = fun(x);
  //@ assert ret2 == (int)band_all(&x[0], N);
  //@ assert ret2 == ret;
 PreRot: ;
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer k; 0 <= k < i ==> x[k] == \at(x[k+1], PreRot);
    loop invariant \forall integer k; i <= k < N ==> x[k] == \at(x[k], PreRot);
    loop assigns i, x[0 .. N-2];
    loop variant N-1-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  //@ assert x[N-1] == \at(x[0], PreRot);
  //@ assert \forall integer k; 0 <= k < N-1 ==> x[k] == \at(x[k+1], PreRot);
  //@ assert band_all(&x[0], N) == \at(band_all(&x[0], N), PreRot);
  ret5 = fun(x);
  //@ assert ret5 == (int)band_all(&x[0], N);
  //@ assert ret5 == ret2;
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
