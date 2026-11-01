#include <stdint.h>
#include <unistd.h>
#include <string.h>
int main()
{
  int i;
  int N=100000;
  int a[N];
  int b[N];
  int c[N];
  //@ loop invariant 0 <= i;
  for(i=0;i<N;i++) {
    a[i]=1;
  }
  return 0;
}
