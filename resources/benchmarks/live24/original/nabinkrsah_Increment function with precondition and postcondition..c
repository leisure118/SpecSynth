#include<stdio.h>
#include<limits.h>
int inc(int n)
{
return n+1;
}
void main()
{
int a=10;
int k=inc(a);
//@ assert k==11;
}