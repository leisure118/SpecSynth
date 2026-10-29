#include <stdio.h>
/*@
  requires a >= 0;
  ensures \result == (a + 1) * b;
  assigns \nothing;
*/
int mul(int a, int b) {
    int x = a, y = b, prod = 0;
    /*@
      loop invariant x >= -1;
      loop invariant prod == (a - x) * b;
      loop assigns x, prod;
      loop variant x;
    */
    while(x >= 0) {
        prod = prod + y;
        x--;
    }
    return prod;
}
int main() {
    int pdt = mul(2, 5);
    //@ assert pdt == 15;
}