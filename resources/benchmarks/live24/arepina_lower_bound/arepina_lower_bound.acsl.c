/*@
  requires \valid_read(a + (0 .. n-1));
  requires \forall integer i, j; 0 <= i <= j < n ==> a[i] <= a[j];
  assigns \nothing;
  ensures \result <= n;
  ensures \forall integer i; 0 <= i < \result ==> a[i] < val;
  ensures \result == n || a[\result] >= val;
*/
unsigned lower_bound(const int *a, unsigned n, int val)
{
   unsigned left = 0;
   unsigned right = n;
   unsigned middle = 0;
   /*@
     loop invariant 0 <= left <= right <= n;
     loop invariant \forall integer i; 0 <= i < left ==> a[i] < val;
     loop invariant \forall integer i; right <= i < n ==> val <= a[i];
     loop assigns left, right, middle;
     loop variant right - left;
   */
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