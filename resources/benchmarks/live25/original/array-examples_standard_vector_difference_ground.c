#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
int main( ) {
  int a[SIZE];
  int b[SIZE];
  int c[SIZE];
  int i = 0;
	for(i = 0; i < SIZE; i++)
	{
	  a[i] = unknown();
		b[i] = unknown();
	}
	i = 0;
  while (i < SIZE) {
    c[i] = a[i] - b[i];
    i = i + 1;
  }
  int x;
  for ( x = 0 ; x < SIZE ; x++ ) {
    //@ assert(c[x] == a[x] - b[x]  );
  }
  return 0;
}
