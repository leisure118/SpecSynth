#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown(void);
#define N 100
#define fun xor
#include <assert.h>

/*@ axiomatic XorAcc {
  logic integer xor_acc{L}(int *a, integer n) reads a[0..n-1];

  axiom xor_acc_base{L}: \forall int *a; xor_acc(a, 0) == 0;

  axiom xor_acc_ind{L}: \forall int *a, integer n;
    n >= 1 ==> xor_acc(a, n) == (xor_acc(a, n-1) ^ a[n-1]);

  axiom xor_swap_first_two{L1,L2}: \forall int *a, integer n;
    n >= 2 ==>
    \at(a[0], L2) == \at(a[1], L1) ==>
    \at(a[1], L2) == \at(a[0], L1) ==>
    (\forall integer i; 2 <= i < n ==> \at(a[i], L2) == \at(a[i], L1)) ==>
    xor_acc{L2}(a, n) == xor_acc{L1}(a, n);

  axiom xor_rotate_left{L1,L2}: \forall int *a, integer n;
    n >= 1 ==>
    (\forall integer i; 0 <= i < n-1 ==> \at(a[i], L2) == \at(a[i+1], L1)) ==>
    \at(a[n-1], L2) == \at(a[0], L1) ==>
    xor_acc{L2}(a, n) == xor_acc{L1}(a, n);

  axiom xor_acc_range{L}: \forall int *a, integer n;
    n >= 0 ==> -2147483648 <= xor_acc(a, n) <= 2147483647;
}
*/

/*@
  requires \valid(x+(0..99));
  assigns \nothing;
  ensures \result == xor_acc(x, 100);
*/
int xor (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= 100;
    loop invariant res == xor_acc(x, i);
    loop assigns i, res;
    loop variant 100 - i;
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
    loop invariant 0 <= i <= 100;
    loop assigns i, x[0..99];
    loop variant 100 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
 L1: ;
  temp=x[0];x[0] = x[1]; x[1] = temp;
 L2: ;
  //@ assert \at(x[0],L2) == \at(x[1],L1);
  //@ assert \at(x[1],L2) == \at(x[0],L1);
  //@ assert \forall integer i; 2 <= i < 100 ==> \at(x[i],L2) == \at(x[i],L1);
  //@ assert xor_acc{L2}(&x[0], 100) == xor_acc{L1}(&x[0], 100);
  //@ assert ret == xor_acc{L1}(&x[0], 100);
  ret2 = fun(x);
  //@ assert ret2 == xor_acc{L2}(&x[0], 100);
  //@ assert ret == ret2;
 L3: ;
  temp=x[0];
  /*@
    loop invariant 0 <= i <= 99;
    loop invariant temp == \at(x[0],L3);
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1],L3);
    loop invariant \forall integer j; i <= j < 100 ==> x[j] == \at(x[j],L3);
    loop assigns i, x[0..98];
    loop variant 99-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
 L4: ;
  //@ assert \forall integer i; 0 <= i < 99 ==> \at(x[i],L4) == \at(x[i+1],L3);
  //@ assert \at(x[99],L4) == \at(x[0],L3);
  //@ assert xor_acc{L4}(&x[0], 100) == xor_acc{L3}(&x[0], 100);
  //@ assert ret == xor_acc{L3}(&x[0], 100);
  ret5 = fun(x);
  //@ assert ret5 == xor_acc{L4}(&x[0], 100);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
