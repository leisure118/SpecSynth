#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define size 100000
int main()
{
  int a[size];
  int b[size];
  int i = 0;
  int j = 0;
  /*@
    loop invariant 0 <= i <= 100000;
    loop assigns i, b[0 .. 99999];
    loop variant 100000 - i;
  */
  while( i < size )
  {
	b[i] = unknown();
    i = i+1;
  }
  i = 1;
  /*@
    loop invariant 0 <= j <= 50000;
    loop invariant i == 2*j + 1;
    loop invariant \forall integer k; 0 <= k < j ==> a[k] == b[2*k+1];
    loop assigns i, j, a[0 .. 49999];
    loop variant 100000 - i;
  */
  while( i < size )
  {
	a[j] = b[i];
        i = i+2;
        j = j+1;
  }
  i = 1;
  j = 0;
  /*@
    loop invariant 0 <= j <= 50000;
    loop invariant i == 2*j + 1;
    loop invariant \forall integer k; 0 <= k < 50000 ==> a[k] == b[2*k+1];
    loop assigns i, j;
    loop variant 100000 - i;
  */
  while( i < size )
  {
	//@ assert(a[j] == b[2*j+1] );
        i = i+2;
        j = j+1;
  }
  return 0;
}
