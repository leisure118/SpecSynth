#include <assert.h>

/*@ assigns \nothing; */
int unknown1();
/*@ assigns \nothing; */
int unknown2();
/*@ assigns \nothing; */
int unknown3();
/*@ assigns \nothing; */
int unknown4();

/*
 * Taken from "Counterexample Driven Refinement for Abstract Interpretation" (TACAS'06) by Gulavani
 */
/*@
requires n > 0;
*/
void foo(int n) {
  int x = 0;
  int m = 0;
  /*@
    loop invariant 0 <= x <= n;
    loop invariant 0 <= m < n;
    loop assigns x, m;
    loop variant n - x;
  */
  while (x < n) {
    if (unknown1()) {
      m = x;
    }
    x = x + 1;
  }
  if (n > 0) {
    //@ assert(0 <= m && m < n);
  }
}