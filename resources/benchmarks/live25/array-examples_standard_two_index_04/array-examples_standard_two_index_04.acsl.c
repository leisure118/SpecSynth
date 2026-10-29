#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define size 100000
int main( )
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
  i = 1;
  /*@
    loop invariant 0 <= i;
    loop invariant 0 <= j;
    loop invariant i == 4*j + 1;
    loop invariant \forall integer k; 0 <= k < j ==> a[k] == b[4*k+1];
    loop assigns i, j, a[0 .. size-1];
    loop variant size - i;
  */
  while( i < size )
  {
	a[j] = b[i];
        i = i+4;
        j = j+1;
  }
  i = 1;
  j = 0;
  /*@
    loop invariant 0 <= i;
    loop invariant 0 <= j;
    loop invariant i == 4*j + 1;
    loop invariant \forall integer k; 0 <= k < size/4 ==> a[k] == b[4*k+1];
    loop assigns i, j;
    loop variant size - i;
  */
  while( i < size )
  {
	//@ assert(a[j] == b[4*j+1] );
        i = i+4;
        j = j+1;
  }
  return 0;
}
