#include<stdio.h>
#include<limits.h>
/*@
  requires \valid(a) && \valid(b);
  assigns *a;
  ensures *a == \old(*a) + \old(*b);
*/
void function(int* a, int const* b)
{
*a += *b;
}
void main() {
int a = 6;
int b = 4;
L1:
function(&a, &b);
//@assert \at(a,Here)==10 &&  b==4;
//@assert \at(a,L1)==6 && \at(b,L1)==4;
} 