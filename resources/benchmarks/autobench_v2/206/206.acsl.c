#include <stdlib.h>

/*@
  requires n >= 0;
  ensures \result == n*(n+1)/2;
  assigns \nothing;
*/
int sum(int n) {
    int s = 0;
    int k = 0;

    /*@
      loop invariant 0 <= k <= n+1;
      loop invariant s == k*(k-1)/2;
      loop assigns k, s;
      loop variant n+1 - k;
    */
    while(k <= n) {    
        s = s + k;
        k = k + 1;
    }
    return s;
}

int main() {
    int s = sum(5);
    //@ assert s == 15;
}