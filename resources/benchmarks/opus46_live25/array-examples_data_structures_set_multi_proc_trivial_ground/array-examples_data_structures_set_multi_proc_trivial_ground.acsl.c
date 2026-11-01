#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SIZE 100000
/*@
  requires \valid(set+size);
  assigns set[size];
  ensures \result == size + 1;
*/
int insert( int set [] , int size , int value ) {
  set[ size ] = value;
  return size + 1;
}
/*@
  requires size >= 0;
  requires \valid_read(set+(0..size-1));
  assigns \nothing;
  ensures \result == 0 || \result == 1;
  ensures size == 0 ==> \result == 0;
*/
int elem_exists( int set [ ] , int size , int value ) {
  int i;
  /*@
    loop invariant 0 <= i <= size;
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
    loop assigns x, y;
    loop variant n - x;
  */
  for ( x = 0 ; x < n ; x++ ) {
    /*@
      loop invariant x + 1 <= y <= n;
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
    loop invariant n == 0;
    loop assigns v, x, y, n, set[0 .. SIZE-1];
    loop variant SIZE - v;
  */
  for ( v = 0 ; v < SIZE ; v++ ) {
    if ( elem_exists( set , n , values[ v ] ) ) {
      n = insert( set , n , values[ v ] );
    }
    /*@
      loop invariant 0 <= x <= n;
      loop assigns x, y;
      loop variant n - x;
    */
    for ( x = 0 ; x < n ; x++ ) {
      /*@
        loop invariant x + 1 <= y <= n;
        loop assigns y;
        loop variant n - y;
      */
      for ( y = x + 1 ; y < n ; y++ ) {
        //@ assert(set[ x ] != set[ y ]  );
      }
    }
  }
  /*@
    loop invariant 0 <= x <= n;
    loop assigns x, y;
    loop variant n - x;
  */
  for ( x = 0 ; x < n ; x++ ) {
    /*@
      loop invariant x + 1 <= y <= n;
      loop assigns y;
      loop variant n - y;
    */
    for ( y = x + 1 ; y < n ; y++ ) {
      //@ assert(set[ x ] != set[ y ]  );
    }
  }
  return 0;
}
