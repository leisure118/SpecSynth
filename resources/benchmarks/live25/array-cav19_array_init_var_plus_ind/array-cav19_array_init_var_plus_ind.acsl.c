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
    loop invariant \forall integer t; 0 <= t < i ==> a[t] == t*(t-1)/2;
    loop invariant j == i*(i-1)/2;
    loop assigns i, j, x, a[0 .. N-1];
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    x=unknown();
    if(x) break;
    a[i]=j;
    j=j+i;
  }
  /*@
    loop invariant 1 <= k;
    loop invariant k <= i || i == 0;
    loop invariant \forall integer t; 0 <= t < i ==> a[t] == t*(t-1)/2;
    loop assigns k;
    loop variant i - k;
  */
  for(int k=1;k<i;k++){
    //@ assert(a[k]>=0);
  }
  return 0;
}
