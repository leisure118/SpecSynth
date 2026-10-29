/*@ 
   requires \valid(&a[i]);
    requires \valid(&a[j]);
    assigns a[i], a[j];
    ensures a[i] == \old(a[j]);
    ensures a[j] == \old(a[i]);
 */
void swap(int a[], int i, int j);
void reverse_in_place(int a[], int size)
{
   int i;
   for(i = 0; i < (size / 2); ++i) {
      swap(a, i, size - i - 1);
   }
}
#ifdef OUT_OF_TASK
#include <stdio.h>
int main(void)
{
   int a[] = {1,2,3,4,5,6,7,8,9,10};
   int size = sizeof(a) / sizeof(a[0]);
   //@ assert a[0] == 1;
   reverse_in_place(a, size);
   //@ assert a[0] == 10;
}
#endif