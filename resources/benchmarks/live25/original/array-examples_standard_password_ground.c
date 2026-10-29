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
  int i;
  int result = 1;
	for (i = 0; i < SIZE; i++)
	{
	    password[i] = unknown();
			guess[i] = unknown();
	}
  for ( i = 0 ; i < SIZE ; i++ ) {
    if ( password[ i ] != guess[ i ] ) {
      result = 0;
    }
  }
  if ( result ) {
    int x;
    for ( x = 0 ; x < SIZE ; x++ ) {
      //@ assert(password[ x ] == guess[ x ]  );
    }
  }
  return 0;
}
