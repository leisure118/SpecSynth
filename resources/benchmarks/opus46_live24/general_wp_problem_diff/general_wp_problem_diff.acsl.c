#include <limits.h>
/*@
  ensures \result == x - y;
  assigns \nothing;
*/
int diff (int x, int y) {
    return x-y;
}
void main() {
    int t = diff(10, 5);
    //@ assert t == 5;
}
