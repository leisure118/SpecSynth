int spec_sign(int x)
{
   return (x > 0) - (x < 0);
}
#ifdef OUT_OF_TASK
#include <stdio.h>
int main(void)
{
   int res = spec_sign(-10);
   //@ assert res == -1;
   return 0;
}
#endif