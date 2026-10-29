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
  int i = 0;
  int c [SIZE];
  int rv = 1;
	//@ admit \separated(a+(0 .. SIZE-1), b+(0 .. SIZE-1), c+(0 .. SIZE-1));
	/*@
	  loop invariant 0 <= j <= SIZE;
	  loop assigns j, a[0 .. SIZE-1], b[0 .. SIZE-1];
	  loop variant SIZE - j;
	*/
	for (int j = 0; j < SIZE ; j++ ) {
    a[j] = unknown();
		b[j] = unknown();
  }
  /*@
    loop invariant 0 <= i <= SIZE;
    loop invariant \forall integer k; 0 <= k < i ==> c[k] == a[k];
    loop invariant rv == 0 || rv == 1;
	    loop invariant rv == 1 ==> \forall integer k; 0 <= k < i ==> a[k] == b[k];
    loop assigns i, rv, c[0 .. SIZE-1];
    loop variant SIZE - i;
  */
  while ( i < SIZE ) {
    if ( a[i] != b[i] ) {
      rv = 0;
    }
    c[i] = a[i];
    i = i+1;
  }
  int x;
  if ( rv ) {
    /*@
      loop invariant 0 <= x <= SIZE;
      loop invariant \forall integer k; 0 <= k < SIZE ==> a[k] == b[k];
      loop assigns x;
      loop variant SIZE - x;
    */
    for ( x = 0 ; x < SIZE ; x++ ) {
      //@ assert(a[x] == b[x]  );
    }
  }
  /*@
    loop invariant 0 <= x <= SIZE;
    loop invariant \forall integer k; 0 <= k < SIZE ==> c[k] == a[k];
    loop assigns x;
    loop variant SIZE - x;
  */
  for ( x = 0 ; x < SIZE ; x++ ) {
    //@ assert(a[x] == c[x]  );
  }
  return 0;
}
