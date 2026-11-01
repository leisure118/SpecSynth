#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 10000
#define fun bor
#include <assert.h>

/*@ axiomatic BOR {
    logic integer bor_n{L}(int *a, integer n) reads a[0..n-1];

    axiom bor_one{L}: \forall int *a;
      bor_n{L}(a, 1) == \at(a[0], L);

    axiom bor_rec{L}: \forall int *a, integer n; n > 1 ==>
      bor_n{L}(a, n) == (bor_n{L}(a, n-1) | \at(a[n-1], L));

    axiom bor_swap{L1, L2}: \forall int *a, integer n;
      n >= 2 ==>
      \at(a[0], L2) == \at(a[1], L1) ==>
      \at(a[1], L2) == \at(a[0], L1) ==>
      (\forall integer k; 2 <= k < n ==> \at(a[k], L2) == \at(a[k], L1)) ==>
      bor_n{L2}(a, n) == bor_n{L1}(a, n);

    axiom bor_rotate{L1, L2}: \forall int *a, integer n;
      n >= 2 ==>
      (\forall integer k; 0 <= k < n-1 ==> \at(a[k], L2) == \at(a[k+1], L1)) ==>
      \at(a[n-1], L2) == \at(a[0], L1) ==>
      bor_n{L2}(a, n) == bor_n{L1}(a, n);
}*/

/*@
  requires \valid_read(x+(0..10000-1));
  assigns \nothing;
  ensures \result == (int)bor_n(x, 10000);
*/
int bor (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= 10000;
    loop invariant res == bor_n(x, i);
    loop assigns i, res;
    loop variant 10000 - i;
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
    loop invariant 0 <= i <= 10000;
    loop assigns i, x[0..10000-1];
    loop variant 10000 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  L1: ;
  temp=x[0];x[0] = x[1]; x[1] = temp;
  //@ assert x[0] == \at(x[1], L1);
  //@ assert x[1] == \at(x[0], L1);
  //@ assert \forall integer k; 2 <= k < 10000 ==> x[k] == \at(x[k], L1);
  //@ assert bor_n(&x[0], 10000) == bor_n{L1}(&x[0], 10000);
  ret2 = fun(x);
  //@ assert ret == ret2;
  L3: ;
  temp=x[0];
  /*@
    loop invariant 0 <= i <= 10000-1;
    loop invariant \forall integer k; 0 <= k < i ==> x[k] == \at(x[k+1], L3);
    loop invariant \forall integer k; i <= k < 10000 ==> x[k] == \at(x[k], L3);
    loop assigns i, x[0..10000-2];
    loop variant 10000-1-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  //@ assert \forall integer k; 0 <= k < 10000-1 ==> x[k] == \at(x[k+1], L3);
  //@ assert x[10000-1] == \at(x[0], L3);
  //@ assert bor_n(&x[0], 10000) == bor_n{L3}(&x[0], 10000);
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
