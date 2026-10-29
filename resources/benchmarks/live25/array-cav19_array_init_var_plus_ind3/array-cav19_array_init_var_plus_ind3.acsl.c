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
    loop invariant j == -i*(i-1)/2;
    loop invariant \forall integer k; 0 <= k < i ==> a[k] == -k*(k-1)/2;
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
    loop invariant k == 4 || k <= i;
    loop invariant \forall integer j; 0 <= j < i ==> a[j] == -j*(j-1)/2;
    loop assigns k;
    loop variant i - k;
  */
  for(int k=4;k<i;k++){
    //@ assert(a[k] <= 0);
  }
  return 0;
}
