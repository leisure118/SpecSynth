#include<limits.h>
/*@
   requires R!=0;
   ensures 0 < \result < 1000000/R;
*/
int unknown(unsigned int R);
int N = 1000000;
int main(){
int i,j=0,k=0,a[N];
unsigned int R=2;
int lim=unknown(R);
//@ assert(0 < lim && lim < N/R);
  /*@
    loop invariant 0 <= i <= N;
    loop invariant 0 <= k;
    loop invariant k <= lim;
    loop invariant j == 0;
    loop invariant k == 0 || 2*k + N/2 < i;
    loop invariant \forall integer m; 0 <= m < i && m <= N/2 ==> a[m] == m + 1;
    loop invariant \forall integer m; 0 <= m < i ==> (a[m] == 0 ==> (m > N/2 && m % 2 == 0));
    loop assigns i, k, a[0 .. N-1];
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    a[i]=i+1;
    if(i>N/2 && k<lim)
       a[i]=i%R;
    if(a[i]==0) k++;
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant 0 <= j;
    loop invariant j == 0 || 2*j + N/2 < i;
    loop invariant \forall integer m; 0 <= m < N ==> (a[m] == 0 ==> (m > N/2 && m % 2 == 0));
    loop assigns i, j;
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    if (a[i]==0) j++;
     //@ assert(j < N/(2*R));
  }
  return 0;
}
