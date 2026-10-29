#include<stdio.h>
/*@
logic integer fact(integer n)=(n<1)? 1:n*fact(n-1);
*/
/*@
  requires n >= 0;
  ensures \result == fact(n);
  assigns \nothing;
*/
int fact(int n)
{
if(n<2)
return 1;
int f=1;
int i;
/*@
  loop invariant 1 <= i <= n+1;
  loop invariant f == fact(i-1);
  loop assigns i, f;
  loop variant n+1 - i;
*/
for(i=1;i<=n;i++)
{
f=f*i;
}
return f;
}
int main()
{
int k=fact(5);
//@ assert k==120;
}