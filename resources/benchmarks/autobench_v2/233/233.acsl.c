// Source: E. De Angelis, F. Fioravanti, J. A. Navas, M. Proietti:
// "Verification of Programs by Combining Iterated Specialization with
// Interpolation", HCVS 2014

#include "assert.h"

int main() {
    int x = 1;
    int y = 0;
    /*@
      loop invariant 0 <= y <= 1000;
      loop invariant x == 1 + y * (y - 1) / 2;
      loop assigns x, y;
      loop variant 1000 - y;
    */
    while (y < 1000) {
        x = x + y;
        y = y + 1;
    }
    //@ assert(x >= y);
    return 0;
}