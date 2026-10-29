#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
/*@
  requires \valid(set+(size));
  assigns set[size];
  ensures \result == size + 1;
  ensures set[size] == value;
*/
int insert( int set [] , int size , int value ) {
  set[ size ] = value;
  return size + 1;
}
/*@
  requires size >= 0;
  requires \valid(set+(0 .. size-1));
  assigns \nothing;
  ensures \result == 0 <==> (\forall integer j; 0 <= j < size ==> set[j] != value);
  ensures \result == 1 <==> (\exists integer j; 0 <= j < size && set[j] == value);
*/
int elem_exists( int set [ ] , int size , int value ) {
  int i;
  /*@
    loop invariant 0 <= i <= size;
    loop invariant \forall integer j; 0 <= j < i ==> set[j] != value;
    loop assigns i;
    loop variant size - i;
  */
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
		/*@
		  loop invariant 0 <= x <= SIZE;
		  loop assigns x, set[0 .. SIZE-1];
		  loop variant SIZE - x;
		*/
		for (x = 0; x < SIZE; x++)
	{
	  set[x] = unknown();
	}
  /*@
    loop invariant 0 <= x <= n;
    loop assigns x;
    loop variant n - x;
  */
  for ( x = 0 ; x < n ; x++ ) {
    /*@
      loop invariant x < y;
      loop invariant \forall integer a, b; 0 <= a < b < n ==> set[a] != set[b];
      loop assigns y;
      loop variant n - y;
    */
    for ( y = x + 1 ; y < n ; y++ ) {
      //@ assert(set[ x ] != set[ y ]  );
    }
  }
  int values[ SIZE ];
  int v;
		/*@
		  loop invariant 0 <= v <= SIZE;
		  loop assigns v, values[0 .. SIZE-1];
		  loop variant SIZE - v;
		*/
		for (v = 0; v < SIZE; v++)
	{
	  values[v] = unknown();
	}
  /*@
    loop invariant 0 <= v <= SIZE;
    loop invariant 0 <= n <= v;
    loop invariant \forall integer a, b; 0 <= a < b < n ==> set[a] != set[b];
    loop assigns v, n, set[0 .. SIZE-1];
    loop variant SIZE - v;
  */
  for ( v = 0 ; v < SIZE ; v++ ) {
    if ( !elem_exists( set , n , values[ v ] ) ) {
      n = insert( set , n , values[ v ] );
    }
  }
  /*@
    loop invariant 0 <= x <= n;
    loop invariant \forall integer a, b; 0 <= a < b < n ==> set[a] != set[b];
    loop assigns x, y;
    loop variant n - x;
  */
  for ( x = 0 ; x < n ; x++ ) {
    /*@
      loop invariant x < y;
      loop invariant \forall integer a, b; 0 <= a < b < n ==> set[a] != set[b];
      loop assigns y;
      loop variant n - y;
    */
    for ( y = x + 1 ; y < n ; y++ ) {
      //@ assert(set[ x ] != set[ y ]  );
    }
  }
  return 0;
}
