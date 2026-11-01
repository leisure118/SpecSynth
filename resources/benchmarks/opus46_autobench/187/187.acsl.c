#include <stdio.h>

/*@
  requires n >= 7;
  assigns \nothing;
  ensures 3 * \result + 4 > n;
  ensures 3 * \result + 1 <= n;
*/
int fun(int n) {
    int i = 7;
    int x = 1;

    /*@
      loop invariant i == 3 * x + 4;
      loop invariant x >= 1;
      loop invariant i <= n + 3;
      loop assigns i, x;
      loop variant n - i;
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