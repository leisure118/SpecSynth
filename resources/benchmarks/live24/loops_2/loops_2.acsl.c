#include <stdlib.h>
/*@
  requires n >= 0 && n < 127;
  assigns \nothing;
  ensures \result == n*(n+1)/2;
*/
int sum(char n) {
    int s = 0;
    char k = 0;
    /*@
      loop invariant 0 <= k <= n+1;
      loop invariant s == k*(k-1)/2;
      loop assigns k, s;
      loop variant (n+1) - k;
    */
    while(k <= n) {    
        s = s + (int)k;
        k = k + 1;
    }
    //@ assert s == (int)((n+1)*(n)/2);
    return (int)s;
}
int main() {
    int s = sum(5);
    //@ assert s == 15;
}