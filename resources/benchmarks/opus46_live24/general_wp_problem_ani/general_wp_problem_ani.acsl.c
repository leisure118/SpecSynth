#include <stdio.h>
/*@
  requires n >= 4;
  assigns \nothing;
  ensures 3 * \result + 1 <= n;
  ensures 3 * \result + 4 > n;
  ensures \result >= 1;
*/
int fun(int n) {
    int i = 7;
    int x = 1;
    /*@
      loop invariant i == 3 * x + 4;
      loop invariant x >= 1;
      loop invariant 3 * x <= n - 1;
      loop assigns i, x;
      loop variant n - i + 3;
    */
    while(i <= n) {
        x += 1;
        i += 3;
    }
    return x;
}
int main() {
    int a = fun(10);
    //@ assert a == 3;
}