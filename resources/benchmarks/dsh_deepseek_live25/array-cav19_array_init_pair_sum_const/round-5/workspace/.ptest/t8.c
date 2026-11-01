#include <stdint.h>
int main()
{
  int i;
  int N=100000;
  int a[N];
  //@ loop invariant \forall integer j; 0 <= j <= i ==> a[j] == 1;
  //@ loop invariant 0 <= i <= N;
  for(i=0;i<N;i++) {
  }
  return 0;
}
