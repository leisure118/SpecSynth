#include <limits.h>
/*@
  requires -20 <= x + y <= 0;
  ensures \result == x + y + 5;
  assigns \nothing;
*/
int function(int x, int y) {
    int res ;
    y += 10 ;
    x -= 5 ;
    res = x + y ;
    //@ assert -15 <= res <= 5;
    return res ;
}
void main() {
    int t = function(-5, 5);
    //@ assert t == 5;
}