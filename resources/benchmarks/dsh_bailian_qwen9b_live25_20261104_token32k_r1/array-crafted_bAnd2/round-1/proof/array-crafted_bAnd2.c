#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 1000
#define fun bAnd
#include <assert.h>
/*@
  requires \valid_read(x + (0 .. N-1));
  assigns \nothing;
  ensures \forall integer j; 0 <= j < N ==> (\result & x[j]) == \result;
  ensures \forall integer v; (\forall integer j; 0 <= j < N ==> (x[j] & v) == v) ==> ((\result & v) == v);
*/
int bAnd (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant \forall integer j; 0 <= j < i ==> (res & x[j]) == res;
    loop invariant \forall integer v; (\forall integer j; 0 <= j < i ==> (x[j] & v) == v) ==> ((res & v) == v);
    loop invariant INT_MIN <= res && res <= INT_MAX;
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
  //@ assert \forall integer j; 0 <= j < N ==> (ret & x[j]) == ret;
  //@ assert \forall integer v; (\forall integer j; 0 <= j < N ==> (x[j] & v) == v) ==> ((ret & v) == v);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  //@ assert \forall integer j; 0 <= j < N ==> (ret & x[j]) == ret;
  //@ assert \forall integer v; (\forall integer j; 0 <= j < N ==> (x[j] & v) == v) ==> ((ret & v) == v);
  ret2 = fun(x);
  //@ assert (ret & ret2) == ret;
  //@ assert (ret & ret2) == ret2;
  //@ assert ret == ret2;
  //@ assert \forall integer j; 0 <= j < N ==> (ret2 & x[j]) == ret2;
  //@ assert \forall integer v; (\forall integer j; 0 <= j < N ==> (x[j] & v) == v) ==> ((ret2 & v) == v);
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N - 1;
    loop invariant \forall integer j; 0 <= j < N - 1 ==> (ret2 & x[j]) == ret2;
    loop assigns i, x[0 .. N - 2];
    loop variant N - 1 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  //@ assert \forall integer j; 0 <= j < N ==> (ret2 & x[j]) == ret2;
  //@ assert \forall integer v; (\forall integer j; 0 <= j < N ==> (x[j] & v) == v) ==> ((ret2 & v) == v);
  ret5 = fun(x);
  //@ assert (ret2 & ret5) == ret2;
  //@ assert (ret2 & ret5) == ret5;
  //@ assert ret2 == ret5;
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}