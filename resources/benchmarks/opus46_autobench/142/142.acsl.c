#include <assert.h>

/*@ assigns \nothing; */
int unknown1();
/*@ assigns \nothing; */
int unknown2();
/*@ assigns \nothing; */
int unknown3();

/*
 * "fragtest_simple" from InvGen benchmark suite
 */

int main(){
  int i, pvlen;
  int t;
  int k = 0;
  int n;
  i = 0;

  //  pkt = pktq->tqh_first;
  /*@
    loop invariant i >= 0;
    loop assigns i;
  */
  while (unknown1())
    i = i + 1;
  
  if (i > pvlen) {
    pvlen = i;
  } else {

  }
  i = 0;

  /*@
    loop invariant k == i;
    loop invariant i >= 0;
    loop invariant k >= 0;
    loop assigns t, i, k;
  */
  while (unknown2()) {
    t = i;
    i = i + 1;
    k = k + 1;
  }
  /*@
    loop assigns \nothing;
  */
  while (unknown3());

  int j = 0;
  n = i;
  /*@
    loop invariant k + j == n;
    loop invariant j >= 0;
    loop invariant j <= n;
    loop invariant n >= 0;
    loop assigns k, i, j;
    loop variant n - j;
  */
  while (1) {
    //@ assert(k >= 0);
    k = k - 1;
    i = i - 1;
    j = j + 1;
    if (j < n) {
    } else {
      break;
    }
  }
  return 0;
}
