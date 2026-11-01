void reverse(int a[], int res[], int size)
{
   int i;
   for(i = size - 1; i >= 0; --i) {
      res[i] = a[size - i - 1];
   }
}
#ifdef OUT_OF_TASK
#include <stdio.h>
int main(void)
{
   int a[] = {1,2,3,4,5,6,7,8,9,10};
   int size = sizeof(a) / sizeof(a[0]);
   reverse(a, b, size);
   //@ assert \forall integer i; 0 <= i < size ==> b[i] == a[size - i - 1];
}
#endif