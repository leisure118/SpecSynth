int main()
{
  int i;
  int N=100000;
  int a[2*N+2];
  for(i=0;i<=N;i++) {
    //@ loop invariant 0 <= i && i <= N+1;
    a[2*i]=0;
    a[2*i+1]=0;
  }
  return 0;
}
