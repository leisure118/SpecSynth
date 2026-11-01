#include <stdint.h>
int main()
{
  int i;
  int N=100000;
  int a[N];
  int b[N];
  int c[N];
  //@ loop invariant 0 <= i <= N;
  for(i=0;i<N;i++) {
    a[i]=1;
    b[i]=2;
  }
  return 0;
}
