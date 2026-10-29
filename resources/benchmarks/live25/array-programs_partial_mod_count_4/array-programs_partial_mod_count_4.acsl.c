int N = 1000000;
int main(){
int i,j=0,a[N];
  unsigned int R=4;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer j; 0 <= j < i && j <= N/2 ==> a[j] == j+1;
    loop invariant \forall integer j; 0 <= j < i && j > N/2 ==> a[j] == j%4;
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
    loop invariant \forall integer k; 0 <= k < N && k > N/2 ==> a[k] == k%4;
    loop invariant (i <= N/2 ==> j == 0) && (i > N/2 ==> j <= (i - 1 - N/2) / 4);
    loop assigns i, j;
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    if (a[i]==0) j++;
     //@assert(j < (N/8));
  }
  return 0;
}
