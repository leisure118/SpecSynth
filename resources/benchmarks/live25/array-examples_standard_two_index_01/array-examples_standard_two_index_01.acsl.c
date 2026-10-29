#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define size 10000
int main()
{
  int a[size];
  int b[size];
  int i = 0;
  int j = 0;
  /*@
    loop invariant 0 <= i <= size;
    loop assigns i, b[0 .. size-1];
    loop variant size - i;
  */
  while( i < size )
  {
	b[i] = unknown();
    i = i+1;
  }
  i = 0;
  /*@
    loop invariant 0 <= i <= size;
    loop invariant 0 <= j <= size;
    loop invariant i == j;
    loop invariant \forall integer k; 0 <= k < j ==> a[k] == b[k];
    loop assigns i, j, a[0 .. size-1];
    loop variant size - i;
  */
  while( i < size )
  {
	a[j] = b[i];
        i = i+1;
        j = j+1;
  }
  i = 0;
  j = 0;
  /*@
    loop invariant 0 <= i <= size;
    loop invariant 0 <= j <= size;
    loop invariant i == j;
    loop invariant \forall integer k; 0 <= k < size ==> a[k] == b[k];
    loop assigns i, j;
    loop variant size - i;
  */
  while( i < size )
  {
	//@ assert(a[j] == b[j] );
        i = i+1;
        j = j+1;
  }
  return 0;
}
