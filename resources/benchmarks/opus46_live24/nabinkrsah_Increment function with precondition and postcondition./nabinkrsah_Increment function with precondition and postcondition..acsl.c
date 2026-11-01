#include<stdio.h>
#include<limits.h>
/*@
  assigns \nothing;
  ensures \result == n + 1;
*/
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