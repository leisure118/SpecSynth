int N = 1000000;
int main(){
int i,j=0,a[N];
  unsigned int R=4;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer k; 0 <= k < i ==> (k <= N/2 ==> a[k] == k + 1);
    loop invariant \forall integer k; 0 <= k < i ==> (k > N/2 ==> a[k] == k % 4);
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
    loop invariant 0 <= j;
    loop invariant \forall integer k; 0 <= k <= N/2 ==> a[k] == k + 1;
    loop invariant \forall integer k; N/2 < k < N ==> a[k] == k % 4;
    loop invariant i <= N/2 + 1 ==> j == 0;
    loop invariant i >= N/2 + 2 ==> j == (i - 1) / 4 - N / 8;
    loop assigns i, j;
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    if (a[i]==0) j++;
     //@assert(j < (N/8));
  }
  return 0;
}
