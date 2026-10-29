#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100000
#define fun bAnd
#include <assert.h>

/*@ axiomatic AndRange {
  logic integer and_range{L}(int *a, integer l, integer h);

  axiom and_range_empty{L}:
    \forall int *a, integer l, integer h;
      l >= h ==> and_range(a, l, h) == -1;

  axiom and_range_single{L}:
    \forall int *a, integer l;
      and_range(a, l, l+1) == a[l];

  axiom and_range_merge{L}:
    \forall int *a, integer l, integer m, integer h;
      l <= m <= h ==> and_range(a, l, h) == (and_range(a, l, m) & and_range(a, m, h));

  axiom and_range_bounds{L}:
    \forall int *a, integer l, integer h;
      -2147483648 <= and_range(a, l, h) <= 2147483647;
}
*/

/*@
  requires \valid(x+(0 .. N-1));
  ensures \result == and_range(x, 0, N);
  assigns \nothing;
*/
int bAnd (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant res == and_range(x, 0, i);
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
  //@ admit \valid(x+(0 .. N-1));
  /*@
    loop invariant 0 <= i <= N;
    loop assigns i, x[0 .. N-1];
    loop variant N - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], LoopEntry);
    loop invariant \forall integer j; i <= j < N ==> x[j] == \at(x[j], LoopEntry);
    loop assigns i, x[0 .. N-2];
    loop variant N-1 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
