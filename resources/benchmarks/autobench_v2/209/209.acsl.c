/*@
  logic integer factorial(integer n) = n <= 0 ? 1 : n * factorial(n-1);
*/

#include <stdio.h>

/*@
  requires n >= 0;
  ensures \result == factorial(n);
  assigns \nothing;
*/
int factorial(int n) {

  int i = 1;
  int f = 1;

  /*@
    loop invariant 1 <= i <= n+1;
    loop invariant f == factorial(i-1);
    loop assigns i, f;
    loop variant n+1 - i;
  */
  while (i <= n)  {
    f = f * i;
    i = i + 1;
  }
  return f;
}

// write a test
void main() {
  int t = factorial(5);
  //@ assert t == 120;
}