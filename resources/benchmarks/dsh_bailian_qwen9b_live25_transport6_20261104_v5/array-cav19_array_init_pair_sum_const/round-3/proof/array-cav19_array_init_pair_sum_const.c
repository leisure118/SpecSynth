int main()
{
  int i;
  int N=100000;
  int a[N];
  int b[N];
  int c[N];
/*@ loop invariant 0 <= i <= N;
    loop invariant \forall integer k; 0 <= k < i ==> a[k] == 1;
    loop invariant \forall integer k; 0 <= k < i ==> b[k] == 2;
    loop invariant \forall integer k; i <= k < N ==> a[k] == \at(a[k], LoopEntry);
    loop invariant \forall integer k; i <= k < N ==> b[k] == \at(b[k], LoopEntry);
    loop assigns i, a[0..N-1], b[0..N-1];
    loop variant N - i;
*/
  for(i=0;i<N;i++) {
    a[i]=1;
    b[i]=2;
  }
/*@ loop invariant 0 <= i <= N;
    loop invariant \forall integer k; 0 <= k < i ==> c[k] == 3;
    loop invariant \forall integer k; i <= k < N ==> c[k] == \at(c[k], LoopEntry);
    loop assigns i, c[0..N-1];
    loop variant N - i;
*/
  for(i=0;i<N;i++){
    c[i]=a[i]+b[i];
  }
/*@ loop invariant 1 <= i <= N;
    loop invariant \forall integer k; 0 <= k < N ==> c[k] == 3;
    loop assigns i;
    loop variant N - i;
*/
  for(i=1;i<N;i++){
    //@ assert(c[i] >= 3);
  }
  return 0;
}
