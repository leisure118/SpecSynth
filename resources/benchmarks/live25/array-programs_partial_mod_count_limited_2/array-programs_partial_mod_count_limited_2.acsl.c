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
    loop invariant k <= lim;
    loop invariant \forall integer j; 0 <= j < i && a[j] == 0 ==> j%R == 0 && j > N/2;
    loop invariant (i <= N/2+1 ==> k == 0) && (i > N/2+1 ==> k <= (i - N/2 - 1)/R);
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
    loop invariant \forall integer t; 0 <= t < N && a[t] == 0 ==> t%R == 0 && t > N/2;
    loop invariant (i <= N/2+1 ==> j == 0) && (i > N/2+1 ==> j <= (i - N/2 - 1)/R);
    loop assigns i, j;
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    if (a[i]==0) j++;
     //@ assert(j < N/(2*R));
  }
  return 0;
}
