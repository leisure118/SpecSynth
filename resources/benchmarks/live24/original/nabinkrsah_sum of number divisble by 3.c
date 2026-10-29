#include<stdio.h>
int dsum(int n)
{
int i=1;
int sum=0;
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