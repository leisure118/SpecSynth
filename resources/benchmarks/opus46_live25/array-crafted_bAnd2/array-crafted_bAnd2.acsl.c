#include<limits.h>

/*@ axiomatic BandProps {
  axiom band_comm:
    \forall integer a, b; (a & b) == (b & a);

  axiom band_assoc:
    \forall integer a, b, c; ((a & b) & c) == (a & (b & c));

  axiom band_idemp:
    \forall integer a; (a & a) == a;
}
*/

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
  ensures \forall integer j; 0 <= j < N ==> ((\result & x[j]) == \result);
  ensures \forall integer v; (\forall integer j; 0 <= j < N ==> ((v & x[j]) == v)) ==> ((v & \result) == v);
*/
int bAnd (int x[N])
{
  int i;
  int res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant \forall integer j; 0 <= j < i ==> ((res & x[j]) == res);
    loop invariant \forall integer v; (\forall integer j; 0 <= j < i ==> ((v & x[j]) == v)) ==> ((v & res) == v);
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
  int i;
  /*@
    loop invariant 0 <= i <= N;
    loop assigns i, x[0 .. N-1];
    loop variant N - i;
  */
  for (i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
 L1: ;
  temp=x[0];x[0] = x[1]; x[1] = temp;
  //@ assert (ret & x[0]) == ret;
  //@ assert (ret & x[1]) == ret;
  //@ assert \forall integer j; 0 <= j < N ==> ((ret & x[j]) == ret);
  ret2 = fun(x);
  //@ assert (ret & ret2) == ret;
  //@ assert \forall integer j; 0 <= j < N ==> ((ret2 & \at(x[j], L1)) == ret2);
  //@ assert (ret2 & ret) == ret2;
  //@ assert ret == ret2;
 L2: ;
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], L2);
    loop invariant \forall integer j; i <= j < N ==> x[j] == \at(x[j], L2);
    loop assigns i, x[0 .. N-2];
    loop variant N - 1 - i;
  */
  for(i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  //@ assert x[N-1] == \at(x[0], L2);
  //@ assert \forall integer j; 0 <= j < N-1 ==> x[j] == \at(x[j+1], L2);
  //@ assert \forall integer j; 0 <= j < N ==> ((ret & x[j]) == ret);
  ret5 = fun(x);
  //@ assert (ret & ret5) == ret;
  //@ assert \forall integer j; 1 <= j < N ==> (\at(x[j], L2) == x[j-1]);
  //@ assert \at(x[0], L2) == x[N-1];
  //@ assert \forall integer j; 1 <= j < N ==> ((ret5 & \at(x[j], L2)) == ret5);
  //@ assert (ret5 & \at(x[0], L2)) == ret5;
  //@ assert \forall integer j; 0 <= j < N ==> ((ret5 & \at(x[j], L2)) == ret5);
  //@ assert (ret5 & ret2) == ret5;
  //@ assert ret5 == ret;
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
