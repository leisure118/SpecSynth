#include<stdio.h>
/*@
logic integer fact(integer n)=(n<1)? 1:n*fact(n-1);
*/
int fact(int n)
{
if(n<2)
return 1;
int f=1;
int i;
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