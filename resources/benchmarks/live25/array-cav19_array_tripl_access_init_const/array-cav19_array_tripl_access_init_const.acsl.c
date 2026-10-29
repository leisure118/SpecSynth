int main()
{
  int i;
  int N=100000;
  int a[3*N+1];
  /*@
    loop invariant 0 <= i <= N+1;
    loop invariant \forall integer j; 0 <= j < 3*i && j <= 3*N ==> a[j] == 0;
    loop assigns i, a[0 .. 3*N+2];
    loop variant N+1 - i;
  */
  for(i=0; i<= N; i++) {
    a[3*i] =0;
    a[3*i+1]=0;
    a[3*i+2]=0;
  }
  /*@
    loop invariant 0 <= i <= 3*N+1;
    loop invariant \forall integer j; 0 <= j <= 3*N ==> a[j] == 0;
    loop assigns i;
    loop variant 3*N+1 - i;
  */
  for(i=0;i<=3*N;i++){
    //@ assert(a[i] >= 0);
  }
  return 0;
}
