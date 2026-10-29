int N = 1000000;
int main(){
int i,j=0,a[N];
  unsigned int R=3;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer k; 0 <= k < i && k <= N/2 ==> a[k] == k+1;
    loop invariant \forall integer k; 0 <= k < i && k > N/2 ==> a[k] == k%3;
    loop assigns i, a[0 .. N-1];
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    a[i]=i+1;
    if(i>N/2)
       a[i]=i%R;
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer k; 0 <= k < N && k <= N/2 ==> a[k] == k+1;
    loop invariant \forall integer k; 0 <= k < N && k > N/2 ==> a[k] == k%3;
    loop invariant (i <= N/2 ==> j == 0);
    loop invariant (i > N/2 && i%3 == 0 ==> 3*j <= i - N/2 + 1);
    loop invariant (i > N/2 && i%3 == 1 ==> 3*j <= i - N/2 + 3);
    loop invariant (i > N/2 && i%3 == 2 ==> 3*j <= i - N/2 + 2);
    loop assigns i, j;
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    if (a[i]==0) j++;
     //@assert(j < (N/6)+2);
  }
  return 0;
}
