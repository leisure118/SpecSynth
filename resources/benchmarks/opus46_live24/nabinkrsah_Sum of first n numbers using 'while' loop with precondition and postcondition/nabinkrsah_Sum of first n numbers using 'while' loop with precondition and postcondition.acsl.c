#include<stdio.h>
#include<limits.h>
/*@
  requires n >= 0;
  ensures \result == n*(n+1)/2;
  assigns \nothing;
*/
int add(int n)
{
int i=1;
int s=0;
/*@
  loop invariant 1 <= i <= n+1;
  loop invariant s == (i-1)*i/2;
  loop assigns i, s;
  loop variant n - i + 1;
*/
while(i<=n)
{
s=s+i;
i++;
}
return s;
}
int main()
{
int k;
k=add(5);
//@ assert k==15;
}
