#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define fun bAnd
#include <assert.h>
int N;
/*@
  requires N >= 1;
  requires \valid_read(x + (0 .. N-1));
  assigns \nothing;
  ensures \forall integer j; 0 <= j < N ==> ((\result & x[j]) == \result);
  ensures \forall integer y; (\forall integer j; 0 <= j < N ==> ((y & x[j]) == y)) ==> ((y & \result) == y);
*/
int bAnd (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant \forall integer j; 0 <= j < i ==> ((res & x[j]) == res);
    loop invariant \forall integer y; (\forall integer j; 0 <= j < i ==> ((y & x[j]) == y)) ==> ((y & res) == y);
    loop assigns i, res;
    loop variant N - i;
  */
  for (i = 1; i < N; i++) {
    res = res & x[i];
  }
  return res;
}
/*@
  assigns N;
  ensures \result == 1;
*/
int main ()
{
  N = unknown();
  if (N > 1) {
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
	  for(int i = 0; i < N; i++) 
		{
		  x[i] = unknown();
		}
		ret = fun(x);
		/*@ assert \forall integer j; 0 <= j < N ==> ((ret & x[j]) == ret); */
		/*@ assert \forall integer y; (\forall integer j; 0 <= j < N ==> ((y & x[j]) == y)) ==> ((y & ret) == y); */
    temp=x[0];x[0] = x[1]; x[1] = temp;
		/*@ assert \forall integer j; 0 <= j < N ==> ((ret & x[j]) == ret); */
    ret2 = fun(x);
		/*@ assert \forall integer j; 0 <= j < N ==> ((ret2 & x[j]) == ret2); */
		/*@ assert \forall integer y; (\forall integer j; 0 <= j < N ==> ((y & x[j]) == y)) ==> ((y & ret2) == y); */
		/*@ assert (ret & ret2) == ret; */
		/*@ assert (ret2 & ret) == ret2; */
		/*@ assert ret == ret2; */
    temp=x[0];
    /*@
      loop invariant 0 <= i <= N-1;
      loop invariant \forall integer j; 0 <= j < i ==> x[j] == \old(x[j+1]);
      loop invariant \forall integer j; 0 <= j < N ==> ((ret & x[j]) == ret);
      loop invariant \forall integer j; 0 <= j < N ==> ((ret2 & x[j]) == ret2);
      loop assigns i, x[0 .. N-2];
      loop variant (N-1) - i;
    */
    for(int i =0 ; i<N-1; i++){
       x[i] = x[i+1];
    }
    x[N-1] = temp;
    ret5 = fun(x);
		/*@ assert \forall integer j; 0 <= j < N ==> ((ret5 & x[j]) == ret5); */
		/*@ assert \forall integer y; (\forall integer j; 0 <= j < N ==> ((y & x[j]) == y)) ==> ((y & ret5) == y); */
		/*@ assert \forall integer j; 0 <= j < N ==> ((ret & x[j]) == ret); */
		/*@ assert \forall integer j; 0 <= j < N ==> ((ret2 & x[j]) == ret2); */
		/*@ assert (ret & ret5) == ret; */
		/*@ assert (ret5 & ret) == ret5; */
		/*@ assert ret == ret5; */
    //@ assert !(ret != ret2 || ret !=ret5);
  }
  return 1;
}
