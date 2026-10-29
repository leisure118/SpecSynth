#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int N = 100000;
int main()
{
  int i;
  int j=0;
  int a[N];
  int x=unknown();
  for(i=0;i<N;i++){
    x=unknown();
    if(x) break;
    a[i]=j;
    j=j+i;
  }
  for(int k=1;k<i;k++){
    //@ assert(a[k]>=0);
  }
  return 0;
}
