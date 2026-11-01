#include<stdio.h>
#include<limits.h>
/*@
  assigns \nothing;
  ensures (a % 2 == 0 || a % 3 == 0) ==> \result == 0;
  ensures (a % 2 != 0 && a % 3 != 0) ==> \result == 1;
*/
int div(int a)
{
if(a%2==0 || a%3==0)
return 0;
else 
return 1;
}
int main()
{
int m=div(6);
//@ assert m==0;
}