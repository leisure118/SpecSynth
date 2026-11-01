#include <stdint.h>
int main()
{
  int i;
  int N=100000;
  int a[N];
  int b[N];
  int c[N];
  //@ loop invariant 0 <= i <= N;
  //@ loop invariant \forall integer j; 0 <= j < i ==> a[j] == 1;
  for(i=0;i<N;i++) {
    a[i]=1;
    b[i]=2;
  }
  return 0;
}
