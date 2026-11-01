#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 10
#define fun max
#include <assert.h>
/*@
  requires \valid_read(x + (0 .. N-1));
  assigns \nothing;
  ensures \result >= 0;
  ensures \forall integer i; 0 <= i < N ==> \result >= x[i];
  ensures \result == 0 || (\exists integer i; 0 <= i < N && \result == x[i]);
*/
int max (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant ret >= 0;
    loop invariant ret <= INT_MAX;
    loop invariant \forall integer j; 0 <= j < i ==> ret >= x[j];
    loop invariant ret == 0 || (\exists integer j; 0 <= j < i && ret == x[j]);
    loop assigns i, ret;
    loop variant N - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret < x[i] ? x[i] : ret;
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
    loop invariant \forall integer j; 0 <= j < N ==> ret2 >= x[j];
    loop invariant ret2 >= temp;
    loop invariant ret2 == 0 || ret2 == temp || (\exists integer j; 0 <= j < N && ret2 == x[j]);
    loop assigns i, x[0 .. N-2];
    loop variant N-1-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
