#include<stdio.h>
/*@
  requires n >= 0;
  ensures \result == 3 * n * (n+1) / 2;
  assigns \nothing;
*/
int dsum(int n)
{
int i=1;
int sum=0;
/*@
  loop invariant 1 <= i <= n+1;
  loop invariant sum == 3 * i * (i-1) / 2;
  loop assigns i, sum;
  loop variant n + 1 - i;
*/
for(i=1;i<=n;i++)
{
sum=sum+3*i;
}
return sum;
}
int main()
{
int k=dsum(3);
//@ assert k==18;
}