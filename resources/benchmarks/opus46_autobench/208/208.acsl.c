#include <stdio.h>
#include <math.h>

/*@
  requires n >= 0;
*/
int fun(int n) {
    double y = 0;
    double i = 0;

    /*@
      loop invariant 0 <= i;
      loop invariant i <= n + 1;
      loop invariant y >= 0;
      loop assigns y, i, __fc_errno;
      loop variant n + 1 - (int)i;
    */
    while(i <= n) {
        y = y + pow(2.0, i);
        i = i + 1;
    }
    return y;
}

int main() {
    int res = fun(4);
    //@assert res == 7;
}
