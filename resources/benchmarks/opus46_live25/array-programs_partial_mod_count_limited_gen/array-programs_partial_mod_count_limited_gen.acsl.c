#include<limits.h>
#include<limits.h>
/*@
assigns \nothing;
ensures 1 < \result < 6;
*/
unsigned int unknown1();
/*@
    requires R!=0;
    assigns \nothing;
    ensures 0 < \result < 1000/R;
*/
int unknown2(unsigned int R);
int N = 1000;
int main(){
int i,j=0,k=0,a[N];
unsigned int R=unknown1();
int lim=unknown2(R);
 //@ assert(R>1 && R<6);
//@ assert(0 < lim && lim < N/R);
  /*@
    loop invariant 0 <= i <= N;
    loop invariant 0 <= k <= lim;
    loop invariant i <= N/R ==> k == 0;
    loop invariant i > N/R ==> k <= (i-1)/R - N/(R*R);
    loop invariant \forall integer m; 0 <= m < i ==> (a[m] == 0 ==> (m > N/R && m % R == 0));
    loop invariant \forall integer m; 0 <= m < i ==> (m <= N/R ==> a[m] == m + 1);
    loop assigns i, k, a[0 .. N-1];
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    a[i]=i+1;
    if(i>N/R && k<lim)
       a[i]=i%R;
    if(a[i]==0) k++;
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant 0 <= j;
    loop invariant i <= N/R ==> j == 0;
    loop invariant i > N/R ==> j <= (i-1)/R - N/(R*R);
    loop invariant j * R * R <= N * (R - 1);
    loop invariant \forall integer m; 0 <= m < N ==> (a[m] == 0 ==> (m > N/R && m % R == 0));
    loop assigns i, j;
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    if (a[i]==0) j++;
     //@ assert j * (R * R) <= N * (R - 1);
     //@ assert(j <= ((N*(R-1))/(R*R)));
  }
  return 0;
}
