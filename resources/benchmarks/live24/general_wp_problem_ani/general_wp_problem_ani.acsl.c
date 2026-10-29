#include <stdio.h>
/*@
  requires n >= 4;
  assigns \nothing;
  ensures \result == (n >= 7 ? 2 + (n - 7) / 3 : 1);
*/
int fun(int n) {
    int i = 7;
    int x = 1;
    /*@
      loop invariant 7 <= i;
      loop invariant i <= n + 3;
      loop invariant 3 * (x - 1) == i - 7;
      loop assigns i, x;
      loop variant n + 3 - i;
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