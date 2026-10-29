#include<stdio.h>
#include<limits.h>
/*@
  requires n < INT_MAX;
  ensures \result == n + 1;
  assigns \nothing;
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