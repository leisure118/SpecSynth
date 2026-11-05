#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100
#define fun bor
#include <assert.h>
/*@
	requires \valid_read(x+(0 .. N-1));
	requires N > 0;
	ensures 0 <= \result <= INT_MAX;
	ensures (x[0] & \result) == x[0];
	assigns \nothing;
*/
int bor (int x[N])
{
  int i;
  long long res;
  res = x[0];
/*@
	loop invariant 1 <= i <= N;
	loop invariant 0 <= res <= INT_MAX;
	loop invariant (x[0] & res) == x[0];
	loop invariant \valid_read(x+(0 .. N-1));
	loop assigns i, res;
	loop variant N - i;
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
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
/*@ assert 0 <= ret <= INT_MAX; */
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
/*@ assert 0 <= ret2 <= INT_MAX; */
  ret2 = fun(x);
  temp=x[0];
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
/*@ assert 0 <= ret5 <= INT_MAX; */
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
