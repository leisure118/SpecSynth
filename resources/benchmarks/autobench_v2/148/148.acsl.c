#include <assert.h>
int unknown1();
int unknown2();
int unknown3();
int unknown4();

/*
 * from Invgen test suite
 */
/*@
requires n > 0;
requires k > n;
*/
int foo(int n, int k) {

  int i, j;

  j = 0;
  /*@
    loop invariant 0 <= j <= n;
    loop invariant k == \at(k, Pre) - j;
    loop assigns j, k;
    loop variant n - j;
  */
  while( j < n ) {
    j++;
    k--;
  } 
  //@ assert(k>=0);
  return 0;
}
