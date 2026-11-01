#include<limits.h>
/*@
  logic integer xor_all(int *a, integer n) =
    n <= 0 ? 0 : xor_all(a, n-1) ^ a[n-1];
*/
/*@ axiomatic XorProperties {
  axiom xor_comm: \forall integer a, b; (a ^ b) == (b ^ a);
  axiom xor_assoc: \forall integer a, b, c; ((a ^ b) ^ c) == (a ^ (b ^ c));
  axiom xor_self: \forall integer a; (a ^ a) == 0;
  axiom xor_zero_l: \forall integer a; (0 ^ a) == a;
  axiom xor_zero_r: \forall integer a; (a ^ 0) == a;
  axiom xor_all_split_2: \forall int *a, integer n;
    n >= 2 ==> xor_all(a, n) == ((a[0] ^ a[1]) ^ xor_all(a+2, n-2));
  axiom xor_all_first: \forall int *a, integer n;
    n >= 1 ==> xor_all(a, n) == (a[0] ^ xor_all(a+1, n-1));
}*/
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 1000
#define fun xor
#include <assert.h>
/*@
  requires \valid(x+(0..999));
  assigns \nothing;
  ensures \result == (int)xor_all(x, 1000);
*/
int xor (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= 1000;
    loop invariant res == xor_all(x, i);
    loop assigns i, res;
    loop variant 1000 - i;
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
    loop invariant 0 <= i <= 1000;
    loop assigns i, x[0..999];
    loop variant 1000 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  temp=x[0];
  /*@
    loop invariant 0 <= i <= 999;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], LoopEntry);
    loop invariant \forall integer j; i <= j < 1000 ==> x[j] == \at(x[j], LoopEntry);
    loop assigns i, x[0..998];
    loop variant 999-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
