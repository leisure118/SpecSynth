#include<stdio.h>
#include<limits.h>
int add(int n)
{
int i=1;
int s=0;
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