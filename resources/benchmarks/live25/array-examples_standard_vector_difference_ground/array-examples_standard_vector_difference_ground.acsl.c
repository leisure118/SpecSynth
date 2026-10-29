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
  //@ admit \separated(a+(0 .. SIZE-1), b+(0 .. SIZE-1), c+(0 .. SIZE-1));
  int i = 0;
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop assigns i, a[0 .. SIZE-1], b[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for(i = 0; i < SIZE; i++)
	{
	  a[i] = unknown();
		b[i] = unknown();
	}
	i = 0;
  /*@
    loop invariant 0 <= i <= SIZE;
    loop invariant \forall integer j; 0 <= j < i ==> c[j] == a[j] - b[j];
    loop assigns i, c[0 .. SIZE-1];
    loop variant SIZE - i;
  */
  while (i < SIZE) {
    c[i] = a[i] - b[i];
    i = i + 1;
  }
  int x;
  /*@
    loop invariant 0 <= x <= SIZE;
    loop invariant \forall integer j; 0 <= j < SIZE ==> c[j] == a[j] - b[j];
    loop assigns x;
    loop variant SIZE - x;
  */
  for ( x = 0 ; x < SIZE ; x++ ) {
    //@ assert(c[x] == a[x] - b[x]  );
  }
  return 0;
}
