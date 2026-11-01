#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 10
#define fun sum
#include <assert.h>

/*@ logic integer psum(int *a, integer n) =
    n <= 0 ? 0 : psum(a, n-1) + a[n-1]; */

/*@
  requires \valid_read(x+(0..9));
  assigns \nothing;
  ensures \result == (int)psum(x, 10);
*/
int sum (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= 10;
    loop invariant (integer)ret == psum(x, i);
    loop assigns i, ret;
    loop variant 10 - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret + x[i];
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
  /*@
    loop invariant 0 <= i <= 10;
    loop assigns i, x[0..9];
    loop variant 10 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  temp=x[0];
  /*@
    loop invariant 0 <= i <= 9;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], LoopEntry);
    loop invariant \forall integer j; i <= j < 10 ==> x[j] == \at(x[j], LoopEntry);
    loop assigns i, x[0..8];
    loop variant 9 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
