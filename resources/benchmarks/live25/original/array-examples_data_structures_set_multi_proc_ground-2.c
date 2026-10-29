#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
int insert( int set [] , int size , int value ) {
  set[ size ] = value;
  return size + 1;
}
int elem_exists( int set [ ] , int size , int value ) {
  int i;
  for ( i = 0 ; i < size ; i++ ) {
    if ( set[ i ] == value ) return 1;
  }
  return 0;
}
int main( ) {
  int n = 0;
  int set[ SIZE ];
  int x;
  int y;
		for (x = 0; x < SIZE; x++)
	{
	  set[x] = unknown();
	}
  for ( x = 0 ; x < n ; x++ ) {
    for ( y = x + 1 ; y < n ; y++ ) {
      //@ assert(set[ x ] != set[ y ]  );
    }
  }
  int values[ SIZE ];
  int v;
		for (v = 0; v < SIZE; v++)
	{
	  values[v] = unknown();
	}
  for ( v = 0 ; v < SIZE ; v++ ) {
    if ( !elem_exists( set , n , values[ v ] ) ) {
      n = insert( set , n , values[ v ] );
    }
  }
  for ( x = 0 ; x < n ; x++ ) {
    for ( y = x + 1 ; y < n ; y++ ) {
      //@ assert(set[ x ] != set[ y ]  );
    }
  }
  return 0;
}
