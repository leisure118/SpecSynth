#include<limits.h>
/*@
  requires x >= 0;
  assigns \nothing;
  ensures \result == x;
*/
int test(int x) {
    int a = x;
    int y = 0;
    /*@
      loop invariant a >= 0 && y + a == x;
      loop assigns a, y;
      loop variant a;
    */
    while(a != 0) {
        y = y + 1;
        a = a - 1;
    }
    return y;
}
int main() {
    int num = test(3);
    //@ assert num == 3;
    return 0;
}
