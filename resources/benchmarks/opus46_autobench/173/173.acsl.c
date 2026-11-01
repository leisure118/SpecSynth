#include <assert.h>
/*@ assigns \nothing; */
int unknown1();
/*@ assigns \nothing; */
int unknown2();

/*@
requires flag > 0;
*/
void foo(int flag) {
  int i, j, k;
  j = 1;
  if (flag) {
    i = 0;
  } else {
    i = 1;
  }

  /*@
    loop invariant i % 2 == 0;
    loop invariant j == i + 1;
    loop assigns i, j;
  */
  while (unknown1()) {
    i += 2;
    if (i % 2 == 0) {
      j += 2;
    } else j++;
  }

  int a = 0;
  int b = 0;

  /*@
    loop invariant a >= 0;
    loop invariant b == a;
    loop invariant j == i + 1;
    loop assigns a, b;
  */
  while (unknown2()) {
    a++;
    b += (j - i);
  }
  if (flag) {
    //@ assert(a == b);
  }
}