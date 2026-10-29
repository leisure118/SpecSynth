unsigned lower_bound(const int *a, unsigned n, int val)
{
   unsigned left = 0;
   unsigned right = n;
   unsigned middle = 0;
   while (left < right) {
      middle = left + (right - left) / 2;
      if (a[middle] < val) {
         //@ assert \forall integer i; 0 <= i < middle+1 ==> a[i] < val;
         left = middle + 1;
      } else right = middle;
   }
   return left;
}
#ifdef OUT_OF_TASK
#include <stdio.h>
#define ARRAY_SIZE(array) (sizeof(array)/sizeof((array)[0]))
int main(void)
{
   int a[] = {0};
   int b[] = {0,1};
   int c[] = {0,1,2,3,4,5};
   int res;
   res = lower_bound(a, ARRAY_SIZE(a), 0);
   printf("res: %d\n", res);
   res = lower_bound(b, ARRAY_SIZE(b), 1);
   printf("res: %d\n", res);
   res = lower_bound(c, ARRAY_SIZE(c), 10);
   printf("res: %d\n", res);
}
#endif