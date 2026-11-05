#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int N = 100000;
int main()
{
  int i;
  int j=0;
  int a[N];
  int x=unknown();
  /*@
    loop invariant 0 <= i <= N;
    loop invariant j <= 0;
    loop invariant \forall integer t; 0 <= t < i ==> a[t] <= 0;
    loop assigns i, j, x, a[0 .. N-1];
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    x=unknown();
    if(x) break;
    a[i]=j;
    j=j-i;
  }
  /*@
    loop invariant 4 <= k;
    loop invariant \forall integer t; 0 <= t < i ==> a[t] <= 0;
    loop assigns k;
    loop variant i - k;
  */
  for(int k=4;k<i;k++){
    //@ assert(a[k] <= 0);
  }
  return 0;
}