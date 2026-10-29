unsigned distance(unsigned a, unsigned b)
{
   return (a > b) ? (a - b) : (b - a);
}
#ifdef OUT_OF_TASK
#include <stdio.h>
int main(void)
{
   int a = distance(5, 3);
   //@ assert a == 2;
   int b = distance(3, 5);
   //@ assert b == 2;
}
#endif