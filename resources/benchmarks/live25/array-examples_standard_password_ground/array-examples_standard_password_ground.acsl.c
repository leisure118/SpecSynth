#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
int main( ) {
  int password[ SIZE ];
  int guess[ SIZE ];
  //@ admit \separated(password+(0 .. SIZE-1), guess+(0 .. SIZE-1));
  int i;
  int result = 1;
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop assigns i, password[0 .. SIZE-1], guess[0 .. SIZE-1];
	  loop variant SIZE - i;
	*/
	for (i = 0; i < SIZE; i++)
	{
	    password[i] = unknown();
			guess[i] = unknown();
	}
  /*@
    loop invariant 0 <= i <= SIZE;
    loop invariant result == 0 || result == 1;
    loop invariant (result == 1) ==> (\forall integer j; 0 <= j < i ==> password[j] == guess[j]);
    loop invariant (result == 0) ==> (\exists integer j; 0 <= j < i && password[j] != guess[j]);
    loop assigns i, result;
    loop variant SIZE - i;
  */
  for ( i = 0 ; i < SIZE ; i++ ) {
    if ( password[ i ] != guess[ i ] ) {
      result = 0;
    }
  }
  if ( result ) {
    int x;
    /*@
      loop invariant 0 <= x <= SIZE;
      loop invariant \forall integer j; 0 <= j < SIZE ==> password[j] == guess[j];
      loop assigns x;
      loop variant SIZE - x;
    */
    for ( x = 0 ; x < SIZE ; x++ ) {
      //@ assert(password[ x ] == guess[ x ]  );
    }
  }
  return 0;
}
