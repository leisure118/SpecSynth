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
    loop invariant rv == 0 || rv == 1;
    loop invariant rv == 1 ==> (\forall integer j; 0 <= j < i ==> a[j] == b[j]);
    loop invariant \forall integer j; 0 <= j < i ==> c[j] == a[j];
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
      loop invariant \forall integer j; 0 <= j < SIZE ==> a[j] == b[j];
      loop assigns x;
      loop variant SIZE - x;
    */
    for ( x = 0 ; x < SIZE ; x++ ) {
      //@ assert(a[x] == b[x]  );
    }
  }
  /*@
    loop invariant 0 <= x <= SIZE;
    loop invariant \forall integer j; 0 <= j < SIZE ==> c[j] == a[j];
    loop assigns x;
    loop variant SIZE - x;
  */
  for ( x = 0 ; x < SIZE ; x++ ) {
    //@ assert(a[x] == c[x]  );
  }
  return 0;
}
